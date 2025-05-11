export class STTService {
    static async transcribe(audioBlob) {
        const formData = new FormData();
        formData.append('file', audioBlob, 'audio.wav');

        const response = await fetch('http://localhost:8000/stt/transcribe', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('STT Error');
        return (await response.json()).text;
    }
}