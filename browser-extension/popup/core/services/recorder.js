export class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.isRecording = false;
    }

    async toggleRecording() {
        if (this.isRecording) {
            return this.stop();
        }
        return this.start();
    }

    async start() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    noiseSuppression: true,
                    echoCancellation: true
                }
            });

            this.mediaRecorder = new MediaRecorder(this.stream);
            this.audioChunks = [];
            this.isRecording = true;

            this.mediaRecorder.ondataavailable = (e) => {
                this.audioChunks.push(e.data);
            };

            this.mediaRecorder.start();
            return new Promise((resolve) => {
                this.mediaRecorder.onstop = () => {
                    resolve(new Blob(this.audioChunks, { type: 'audio/webm; codecs=opus' }));
                };
            });

        } catch (err) {
            this.cleanup();
            throw err;
        }
    }

    async stop() {
        if (!this.isRecording) return null;
        this.mediaRecorder.stop();
        this.cleanup();
        this.isRecording = false;
    }

    cleanup() {
        this.stream?.getTracks().forEach(track => {
            track.stop();
            track.enabled = false;
        });
        this.mediaRecorder = null;
        this.audioChunks = [];
    }
}