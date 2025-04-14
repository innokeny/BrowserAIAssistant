export class TTSService {
    static async speak(text) {
        try {
            // Останавливаем предыдущее воспроизведение
            if (this.currentAudio) {
                this.currentAudio.pause();
                this.currentAudio = null;
            }

            const encodedText = encodeURIComponent(text);
            const response = await fetch('http://localhost:8000/tts/synthesize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, speaker: "baya" })
            });

            if (!response.ok) throw new Error(`TTS Error: ${response.status}`);

            const audioBlob = await response.blob();
            this.currentAudio = new Audio(URL.createObjectURL(audioBlob));

            return new Promise((resolve) => {
                this.currentAudio.onended = resolve;
                this.currentAudio.play();
            });

        } catch (err) {
            console.error('TTS Failed:', err);
            throw err;
        }
    }
}