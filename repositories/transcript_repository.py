import json

from models import TranscriptJob, TranscriptOutput, TranscriptSegment, db


class TranscriptRepository:
    """Persist transcript jobs and their segments."""

    def create_job(
        self,
        user_id,
        source_filename,
        original_filename,
        selected_style,
        provider,
        language_outputs,
    ):
        if not language_outputs:
            raise ValueError('At least one language output is required')

        primary_output = language_outputs[0]
        primary_language = primary_output['language_code']
        job = TranscriptJob(
            user_id=user_id,
            source_filename=source_filename,
            original_filename=original_filename,
            language=primary_language,
            provider=provider,
            transcript_text=primary_output.get('transcript', {}).get('text', ''),
            transcript_payload=json.dumps(
                {
                    'selected_style': selected_style,
                    'provider': provider,
                    'primary_language': primary_language,
                    'languages': [output['language_code'] for output in language_outputs],
                },
                ensure_ascii=False,
            ),
            duration=primary_output.get('transcript', {}).get('duration', 0),
            status='transcribed',
        )
        db.session.add(job)
        db.session.flush()

        for output_index, output in enumerate(language_outputs):
            transcript = output.get('transcript', {})
            transcript_payload = json.dumps(transcript, ensure_ascii=False)
            output_row = TranscriptOutput(
                transcript_job_id=job.id,
                output_index=output_index,
                language_code=output['language_code'],
                transcript_text=transcript.get('text', ''),
                transcript_payload=transcript_payload,
                duration=transcript.get('duration', 0),
                status='transcribed',
                is_primary=output_index == 0,
            )
            db.session.add(output_row)

            if output_index == 0:
                for index, segment in enumerate(transcript.get('segments', [])):
                    start_time = float(segment.get('start', 0.0))
                    end_time = float(segment.get('end', 0.0))
                    segment_duration = segment.get('duration')
                    duration = float(segment_duration) if segment_duration is not None else max(end_time - start_time, 0.0)
                    db.session.add(
                        TranscriptSegment(
                            transcript_job_id=job.id,
                            segment_index=index,
                            start_time=start_time,
                            end_time=end_time,
                            duration=duration,
                            text=segment.get('text', ''),
                        )
                    )

        db.session.commit()
        return job

    def get_jobs_for_user(self, user_id):
        return TranscriptJob.query.filter_by(user_id=user_id).order_by(TranscriptJob.processed_at.desc()).all()

    def get_job(self, job_id, user_id=None):
        query = TranscriptJob.query.filter_by(id=job_id)
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        return query.first()

    def serialize_job(self, job):
        if job is None:
            return None

        outputs = [
            self.serialize_output(output)
            for output in job.outputs
        ]
        primary_output = next((output for output in outputs if output['is_primary']), outputs[0] if outputs else None)
        payload = {}
        if job.transcript_payload:
            try:
                payload = json.loads(job.transcript_payload)
            except json.JSONDecodeError:
                payload = {}

        serialized = {
            'id': job.id,
            'source_filename': job.source_filename,
            'original_filename': job.original_filename,
            'style': payload.get('selected_style', 'meme'),
            'selected_style': payload.get('selected_style', 'meme'),
            'language': job.language,
            'primary_language': payload.get('primary_language', job.language),
            'languages': payload.get('languages') or [output['language_code'] for output in outputs],
            'provider': job.provider,
            'transcript_text': (primary_output or {}).get('transcript_text', job.transcript_text or ''),
            'duration': (primary_output or {}).get('duration', job.duration or 0),
            'status': job.status,
            'processed_at': job.processed_at.isoformat() if job.processed_at else None,
            'updated_at': job.updated_at.isoformat() if getattr(job, 'updated_at', None) else None,
            'segments': (primary_output or {}).get('segments', []),
            'outputs': outputs,
        }

        if not serialized['segments'] and job.segments:
            serialized['segments'] = [
                {
                    'id': segment.id,
                    'segment_index': segment.segment_index,
                    'start': segment.start_time,
                    'end': segment.end_time,
                    'duration': segment.duration,
                    'text': segment.text,
                }
                for segment in job.segments
            ]

        return serialized

    def serialize_output(self, output):
        payload = {}
        if output.transcript_payload:
            try:
                payload = json.loads(output.transcript_payload)
            except json.JSONDecodeError:
                payload = {}

        return {
            'id': output.id,
            'language_code': output.language_code,
            'language': output.language_code,
            'transcript_text': output.transcript_text or '',
            'duration': output.duration or 0,
            'status': output.status,
            'srt_filename': output.srt_filename,
            'burned_video_filename': output.burned_video_filename,
            'processed_at': output.processed_at.isoformat() if output.processed_at else None,
            'updated_at': output.updated_at.isoformat() if getattr(output, 'updated_at', None) else None,
            'is_primary': output.is_primary,
            'segments': [
                {
                    'id': segment.get('id'),
                    'segment_index': index,
                    'start': float(segment.get('start', 0.0)),
                    'end': float(segment.get('end', 0.0)),
                    'duration': segment.get('duration'),
                    'text': segment.get('text', ''),
                }
                for index, segment in enumerate(payload.get('segments', []))
            ],
        }

    def get_output(self, job_id, language_code=None, user_id=None):
        query = TranscriptOutput.query.filter_by(transcript_job_id=job_id)
        if language_code is not None:
            query = query.filter_by(language_code=language_code)
        job = self.get_job(job_id, user_id=user_id)
        if job is None:
            return None
        output = query.order_by(TranscriptOutput.output_index.asc()).first()
        if output is None and language_code is None and job.outputs:
            output = next((item for item in job.outputs if item.is_primary), job.outputs[0])
        return output

    def update_segments(self, job_id, segments, user_id=None, language_code=None):
        job = self.get_job(job_id, user_id=user_id)
        if job is None:
            return None

        output = self.get_output(job_id, language_code=language_code, user_id=user_id)
        if output is None:
            return None

        existing_segments = list(job.segments)
        for index, incoming in enumerate(segments):
            start_time = float(incoming.get('start', 0.0))
            end_time = float(incoming.get('end', start_time))
            duration = incoming.get('duration')
            duration = float(duration) if duration is not None else max(end_time - start_time, 0.0)
            text = incoming.get('text', '').strip()

            if index < len(existing_segments) and output.is_primary:
                segment = existing_segments[index]
                segment.segment_index = index
                segment.start_time = start_time
                segment.end_time = end_time
                segment.duration = duration
                segment.text = text
            elif output.is_primary:
                db.session.add(
                    TranscriptSegment(
                        transcript_job_id=job.id,
                        segment_index=index,
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration,
                        text=text,
                    )
                )

        if output.is_primary and len(existing_segments) > len(segments):
            for segment in existing_segments[len(segments):]:
                db.session.delete(segment)

        output.transcript_text = ' '.join(segment.get('text', '').strip() for segment in segments if segment.get('text'))
        output.transcript_payload = json.dumps(
            {
                'text': output.transcript_text,
                'language': output.language_code,
                'duration': output.duration,
                'segments': segments,
            },
            ensure_ascii=False,
        )
        output.status = 'reviewed'
        if output.is_primary:
            job.transcript_text = output.transcript_text
            job.transcript_payload = json.dumps(
                {
                    'selected_style': job.selected_style,
                    'provider': job.provider,
                    'primary_language': output.language_code,
                    'languages': job.target_languages,
                },
                ensure_ascii=False,
            )
            job.status = 'reviewed'
        db.session.commit()
        return job

    def rebuild_transcript(self, job, language_code=None):
        output = self.get_output(job.id, language_code=language_code, user_id=job.user_id)
        if output is None:
            payload = {}
            if job.transcript_payload:
                try:
                    payload = json.loads(job.transcript_payload)
                except json.JSONDecodeError:
                    payload = {}
            payload['segments'] = [
                {
                    'id': segment.id,
                    'start': segment.start_time,
                    'end': segment.end_time,
                    'duration': segment.duration,
                    'text': segment.text,
                }
                for segment in job.segments
            ]
            payload['text'] = ' '.join(segment['text'] for segment in payload['segments'] if segment.get('text'))
            payload['language'] = job.language
            payload['duration'] = job.duration or (payload['segments'][-1]['end'] if payload['segments'] else 0)
            return payload

        payload = {}
        if output.transcript_payload:
            try:
                payload = json.loads(output.transcript_payload)
            except json.JSONDecodeError:
                payload = {}

        segments = [
            {
                'id': segment.get('id'),
                'start': float(segment.get('start', 0.0)),
                'end': float(segment.get('end', 0.0)),
                'duration': segment.get('duration'),
                'text': segment.get('text', ''),
            }
            for segment in payload.get('segments', [])
        ]
        payload['segments'] = segments
        payload['text'] = ' '.join(segment['text'] for segment in segments if segment.get('text'))
        payload['language'] = output.language_code
        payload['duration'] = output.duration or (segments[-1]['end'] if segments else 0)
        payload['language_code'] = output.language_code
        return payload
