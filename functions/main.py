import functions_framework
from google.cloud import firestore, texttospeech, storage
from datetime import datetime


@functions_framework.http
def auto_publish_blog(request):
    db = firestore.Client()
    # Get the latest draft
    drafts = db.collection('drafts').order_by('created_at', direction=firestore.Query.DESCENDING).limit(1).stream()
    for draft in drafts:
        draft_data = draft.to_dict()
        # Add published_at timestamp
        draft_data['published_at'] = datetime.utcnow()
        # Move to posts collection (instead of published)
        db.collection('posts').add(draft_data)
        # Delete the draft
        db.collection('drafts').document(draft.id).delete()
        return ('Published latest draft!', 200)
    return ('No drafts found.', 200)

def generate_tts_audio(text, output_file, voice_name, language_code):
    tts_client = texttospeech.TextToSpeechClient()
    storage_client = storage.Client()
    bucket = storage_client.bucket('radioquest-e1f5a-audio')
    synthesis_input = texttospeech.SynthesisInput(text=text[:5000])
    voice = texttospeech.VoiceSelectionParams(language_code=language_code, name=voice_name)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,
        sample_rate_hertz=16000
    )
    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    blob = bucket.blob(output_file)
    blob.upload_from_string(response.audio_content, content_type='audio/mpeg')
    public_url = f"https://storage.googleapis.com/{bucket.name}/{output_file}"
    return public_url

# Firestore-triggered function for TTS automation
@functions_framework.cloud_event
def generate_tts_on_new_segment(cloud_event):
    import base64
    data = cloud_event.data
    value = data.get('value', {})
    fields = value.get('fields', {})
    # Determine if this is a story segment or quiz
    segment_id = fields.get('segment_id', {}).get('stringValue', 'unknown')
    story_block = fields.get('story_block', {}).get('stringValue', '')
    question = fields.get('question', {}).get('stringValue', '')
    options = fields.get('options', {}).get('mapValue', {}).get('fields', {})
    # Compose TTS text
    tts_text = story_block
    if question:
        tts_text += '\n' + question
    if options:
        for k, v in options.items():
            tts_text += f"\nOption {k}: {v.get('stringValue', '')}"
    # Generate TTS for Swahili and French
    tts_urls = {}
    for lang, (voice, code) in {
        'sw': ('sw-KE-Standard-A', 'sw-KE'),
        'fr': ('fr-FR-Neural2-B', 'fr-FR')
    }.items():
        output_file = f"auto_{segment_id}_{lang}.mp3"
        try:
            url = generate_tts_audio(tts_text, output_file, voice, code)
            tts_urls[lang] = url
        except Exception as e:
            print(f"TTS failed for {segment_id} ({lang}): {e}")
    # Update Firestore with TTS URLs
    db = firestore.Client()
    doc_path = value.get('name', '').split('/documents/')[-1]
    if doc_path:
        db.document(doc_path).update({'tts_audio': tts_urls})
    return 'TTS generated and Firestore updated', 200 