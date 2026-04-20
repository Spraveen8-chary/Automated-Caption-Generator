import json

from models import TranscriptJob, TranscriptSegment, db


class TranscriptRepository:
    """Persist transcript jobs and their segments."""

    def create_job(self, user_id, source_filename, original_filename, language, transcript, provider='gemini'):
        job = TranscriptJob(
            user_id=user_id,
            source_filename=source_filename,
            original_filename=original_filename,
            language=language,
            provider=provider,
            transcript_text=transcript.get('text', ''),
            transcript_payload=json.dumps(transcript, ensure_ascii=False),
            duration=transcript.get('duration', 0),
            status='transcribed',
        )
        db.session.add(job)
        db.session.flush()

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

        return {
            'id': job.id,
            'source_filename': job.source_filename,
            'original_filename': job.original_filename,
            'language': job.language,
            'provider': job.provider,
            'transcript_text': job.transcript_text or '',
            'duration': job.duration or 0,
            'status': job.status,
            'processed_at': job.processed_at.isoformat() if job.processed_at else None,
            'updated_at': job.updated_at.isoformat() if getattr(job, 'updated_at', None) else None,
            'segments': [
                {
                    'id': segment.id,
                    'segment_index': segment.segment_index,
                    'start': segment.start_time,
                    'end': segment.end_time,
                    'duration': segment.duration,
                    'text': segment.text,
                }
                for segment in job.segments
            ],
        }

    def update_segments(self, job_id, segments, user_id=None):
        job = self.get_job(job_id, user_id=user_id)
        if job is None:
            return None

        existing_segments = list(job.segments)
        for index, incoming in enumerate(segments):
            start_time = float(incoming.get('start', 0.0))
            end_time = float(incoming.get('end', start_time))
            duration = incoming.get('duration')
            duration = float(duration) if duration is not None else max(end_time - start_time, 0.0)
            text = incoming.get('text', '').strip()

            if index < len(existing_segments):
                segment = existing_segments[index]
                segment.segment_index = index
                segment.start_time = start_time
                segment.end_time = end_time
                segment.duration = duration
                segment.text = text
            else:
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

        if len(existing_segments) > len(segments):
            for segment in existing_segments[len(segments):]:
                db.session.delete(segment)

        job.transcript_text = ' '.join(segment.get('text', '').strip() for segment in segments if segment.get('text'))
        job.transcript_payload = json.dumps(
            {
                'text': job.transcript_text,
                'language': job.language,
                'language_name': None,
                'duration': job.duration,
                'segments': segments,
            },
            ensure_ascii=False,
        )
        job.status = 'reviewed'
        db.session.commit()
        return job

    def rebuild_transcript(self, job):
        payload = {}
        if job.transcript_payload:
            try:
                payload = json.loads(job.transcript_payload)
            except json.JSONDecodeError:
                payload = {}

        segments = [
            {
                'id': segment.id,
                'start': segment.start_time,
                'end': segment.end_time,
                'duration': segment.duration,
                'text': segment.text,
            }
            for segment in job.segments
        ]
        payload['segments'] = segments
        payload['text'] = ' '.join(segment['text'] for segment in segments if segment.get('text'))
        payload['language'] = job.language
        payload['duration'] = job.duration or (segments[-1]['end'] if segments else 0)
        return payload
