import pyaudio
import numpy as np
import wave

# Configurações
CHANNELS = 1
RATE = 48000
CHUNK = 1024
THRESHOLD = 50  # Ajuste o valor conforme necessário para a detecção correta

def voice_detection():
    print("Iniciando aplicação...")
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    print("Pronto para detectar fala. Pressione Ctrl+C para sair.")
    audio_data_vector = []
    count_silencio = 0

    def calculate_rms(audio_data):
        """Função para calcular o RMS de um bloco de áudio com verificação de NaN"""
        rms = np.sqrt(np.mean(np.square(audio_data)))  # RMS correto
        if np.isnan(rms):
            return 1  # Retorna 0 se o cálculo gerar NaN
        return rms

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            # Converte os dados para um array NumPy
            audio_data = np.frombuffer(data, dtype=np.int16)
            rms = calculate_rms(audio_data)  # Calcula o volume (RMS)
            print(f"RMS: {rms}")

            if rms < THRESHOLD:
                print(f"Voz detectada! (RMS: {rms})")
                audio_data_vector.append(audio_data)
            else:
                print("Silêncio.")
                count_silencio += 1
                if count_silencio < 10:
                    continue
                # Salvando o áudio em um arquivo WAV quando o silêncio for detectado
                if audio_data_vector:
                    # Concatenando todos os pedaços de áudio
                    audio_data_vector = np.concatenate(audio_data_vector)
                    
                    # Salvando o arquivo WAV
                    with wave.open("gravacao.wav", "wb") as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
                        wf.setframerate(RATE)
                        wf.writeframes(audio_data_vector.tobytes())
                    print("Áudio salvo em gravacao.wav")
                    
                break
    except KeyboardInterrupt:
        print("Encerrando.")
        if audio_data_vector:
            # Concatenando todos os pedaços de áudio
            audio_data_vector = np.concatenate(audio_data_vector)
            
            # Salvando o arquivo WAV
            with wave.open("gravacao.wav", "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
                wf.setframerate(RATE)
                wf.writeframes(audio_data_vector.tobytes())
            print("Áudio salvo em gravacao.wav")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

# voice_detection()