import json
from datetime import date, datetime, time

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Time, Text

from models import User, db

admin_database_bp = Blueprint('admin_database', __name__)

SYSTEM_READONLY_COLUMNS = {
    'created_at',
    'updated_at',
    'processed_at',
    'approved_at',
}


def _require_admin():
    if not getattr(current_user, 'is_admin', False):
        abort(403)


def _table_label(table_name):
    return table_name.replace('_', ' ').title()


def _model_registry():
    registry = {}
    for mapper in db.Model.registry.mappers:
        model = mapper.class_
        table_name = getattr(model, '__tablename__', None)
        if table_name:
            registry[table_name] = model
    return dict(sorted(registry.items(), key=lambda item: item[0]))


def _get_model(table_name):
    model = _model_registry().get(table_name)
    if model is None:
        abort(404)
    return model


def _primary_key_column(model):
    primary_keys = list(model.__table__.primary_key.columns)
    if len(primary_keys) != 1:
        abort(400, description='Only single-column primary keys are supported.')
    return primary_keys[0]


def _display_value(value):
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime('%H:%M:%S')
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _widget_for_column(column):
    if isinstance(column.type, Boolean):
        return 'checkbox'
    if isinstance(column.type, DateTime):
        return 'datetime-local'
    if isinstance(column.type, Date):
        return 'date'
    if isinstance(column.type, Time):
        return 'time'
    if isinstance(column.type, (Text,)) or (getattr(column.type, 'length', None) and column.type.length > 140):
        return 'textarea'
    if isinstance(column.type, (Integer, Float)):
        return 'number'
    return 'text'


def _format_input_value(column, value):
    if value is None:
        return ''
    if isinstance(column.type, DateTime):
        return value.strftime('%Y-%m-%dT%H:%M')
    if isinstance(column.type, Date):
        return value.isoformat()
    if isinstance(column.type, Time):
        return value.strftime('%H:%M:%S')
    if isinstance(column.type, Boolean):
        return bool(value)
    return _display_value(value)


def _is_readonly_column(column):
    return (
        column.primary_key
        or column.name in SYSTEM_READONLY_COLUMNS
        or getattr(column, 'autoincrement', False) is True
        or column.server_default is not None
    )


def _field_spec(column, value=None):
    return {
        'name': column.name,
        'label': column.name.replace('_', ' ').title(),
        'widget': _widget_for_column(column),
        'value': _format_input_value(column, value),
        'checked': bool(value) if isinstance(column.type, Boolean) else False,
        'editable': not _is_readonly_column(column),
        'required': not column.nullable and not _is_readonly_column(column),
        'placeholder': column.name.replace('_', ' ').title(),
    }


def _editable_columns(model):
    return [column for column in model.__table__.columns if not _is_readonly_column(column)]


def _coerce_column_value(column, raw_value, is_checkbox=False):
    if is_checkbox:
        return raw_value

    if raw_value is None:
        return None

    if raw_value == '':
        if isinstance(column.type, (Text,)):
            return ''
        if getattr(column.type, 'length', None) is not None:
            return ''
        return None

    if isinstance(column.type, Integer):
        return int(raw_value)
    if isinstance(column.type, Float):
        return float(raw_value)
    if isinstance(column.type, DateTime):
        return datetime.fromisoformat(raw_value)
    if isinstance(column.type, Date):
        return date.fromisoformat(raw_value)
    if isinstance(column.type, Time):
        return time.fromisoformat(raw_value)
    return raw_value


def _extract_form_payload(model, form):
    payload = {}
    errors = []

    for column in _editable_columns(model):
        is_checkbox = isinstance(column.type, Boolean)
        raw_value = form.get(column.name)
        if is_checkbox:
            payload[column.name] = column.name in form
            continue

        try:
            coerced = _coerce_column_value(column, raw_value)
        except (TypeError, ValueError):
            errors.append(f"Invalid value for {column.name}")
            continue

        if coerced is None and not column.nullable and column.default is None and column.server_default is None:
            errors.append(f"{column.name} is required")
            continue

        payload[column.name] = coerced

    return payload, errors


def _serialize_record(record, model):
    columns = list(model.__table__.columns)
    pk_column = _primary_key_column(model)
    return {
        'pk_name': pk_column.name,
        'pk_value': getattr(record, pk_column.name),
        'values': {
            column.name: _display_value(getattr(record, column.name))
            for column in columns
        },
        'field_specs': [_field_spec(column, getattr(record, column.name)) for column in _editable_columns(model)],
    }


def _table_summaries():
    tables = []
    for table_name, model in _model_registry().items():
        tables.append({
            'name': table_name,
            'label': _table_label(table_name),
            'model_name': model.__name__,
            'count': model.query.count(),
        })
    return tables


def _build_table_context(table_name, edit_id=None):
    model = _get_model(table_name)
    columns = list(model.__table__.columns)
    records = [
        _serialize_record(record, model)
        for record in model.query.order_by(_primary_key_column(model).asc()).all()
    ]

    edit_record = None
    edit_fields = []
    if edit_id is not None:
        record = db.session.get(model, edit_id)
        if record is not None:
            edit_record = _serialize_record(record, model)
            edit_fields = edit_record['field_specs']

    create_fields = [_field_spec(column) for column in _editable_columns(model)]

    return {
        'name': table_name,
        'label': _table_label(table_name),
        'model_name': model.__name__,
        'count': model.query.count(),
        'columns': columns,
        'records': records,
        'pk_name': _primary_key_column(model).name,
        'create_fields': create_fields,
        'edit_record': edit_record,
        'edit_fields': edit_fields,
        'readonly_columns': [column for column in columns if _is_readonly_column(column)],
    }


@admin_database_bp.route('/admin/database')
@login_required
def database_home():
    _require_admin()
    tables = _table_summaries()
    if not tables:
        flash('No database tables are available.', 'error')
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_database.table_view', table_name=tables[0]['name']))


@admin_database_bp.route('/admin/database/<table_name>')
@login_required
def table_view(table_name):
    _require_admin()
    edit_id = request.args.get('edit', type=int)
    tables = _table_summaries()
    selected = _build_table_context(table_name, edit_id=edit_id)
    main_app_url = url_for('index') if 'index' in current_app.view_functions else url_for('admin_dashboard')
    return render_template(
        'admin_database.html',
        tables=tables,
        selected=selected,
        main_app_url=main_app_url,
    )


@admin_database_bp.route('/admin/database/<table_name>/create', methods=['POST'])
@login_required
def create_row(table_name):
    _require_admin()
    model = _get_model(table_name)
    payload, errors = _extract_form_payload(model, request.form)
    if errors:
        flash(' ; '.join(errors), 'error')
        return redirect(url_for('admin_database.table_view', table_name=table_name))

    try:
        record = model(**payload)
        db.session.add(record)
        db.session.commit()
        flash(f'{_table_label(table_name)} row created successfully.', 'success')
    except IntegrityError as error:
        db.session.rollback()
        flash(f'Could not create row: {error.orig}', 'error')
    except Exception as error:
        db.session.rollback()
        flash(f'Could not create row: {error}', 'error')

    return redirect(url_for('admin_database.table_view', table_name=table_name))


@admin_database_bp.route('/admin/database/<table_name>/<int:record_id>/update', methods=['POST'])
@login_required
def update_row(table_name, record_id):
    _require_admin()
    model = _get_model(table_name)
    record = db.session.get(model, record_id)
    if record is None:
        flash('Record not found.', 'error')
        return redirect(url_for('admin_database.table_view', table_name=table_name))

    payload, errors = _extract_form_payload(model, request.form)
    if errors:
        flash(' ; '.join(errors), 'error')
        return redirect(url_for('admin_database.table_view', table_name=table_name, edit=record_id))

    try:
        for key, value in payload.items():
            setattr(record, key, value)
        db.session.commit()
        flash(f'{_table_label(table_name)} row updated successfully.', 'success')
    except IntegrityError as error:
        db.session.rollback()
        flash(f'Could not update row: {error.orig}', 'error')
    except Exception as error:
        db.session.rollback()
        flash(f'Could not update row: {error}', 'error')

    return redirect(url_for('admin_database.table_view', table_name=table_name, edit=record_id))


@admin_database_bp.route('/admin/database/<table_name>/<int:record_id>/delete', methods=['POST'])
@login_required
def delete_row(table_name, record_id):
    _require_admin()
    model = _get_model(table_name)
    record = db.session.get(model, record_id)
    if record is None:
        flash('Record not found.', 'error')
        return redirect(url_for('admin_database.table_view', table_name=table_name))

    if table_name == 'users':
        if getattr(record, 'id', None) == getattr(current_user, 'id', None):
            flash('You cannot delete the account you are currently logged into.', 'error')
            return redirect(url_for('admin_database.table_view', table_name=table_name))

        if getattr(record, 'is_admin', False):
            admin_count = User.query.filter_by(is_admin=True).count()
            if admin_count <= 1:
                flash('At least one admin account must remain in the database.', 'error')
                return redirect(url_for('admin_database.table_view', table_name=table_name))

    try:
        db.session.delete(record)
        db.session.commit()
        flash(f'{_table_label(table_name)} row deleted successfully.', 'success')
    except IntegrityError as error:
        db.session.rollback()
        flash(f'Could not delete row: {error.orig}', 'error')
    except Exception as error:
        db.session.rollback()
        flash(f'Could not delete row: {error}', 'error')

    return redirect(url_for('admin_database.table_view', table_name=table_name))
