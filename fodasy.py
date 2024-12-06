import cv2


import pyaudio

def list_audio_devices():
    p = pyaudio.PyAudio()

    print("Available Audio Devices:\n")
    for i in range(p.get_device_count()):
        device = p.get_device_info_by_index(i)
        print(f"Device Index: {i}")
        print(f"Name: {device['name']}")
        print(f"Max Input Channels: {device['maxInputChannels']}")
        print(f"Max Output Channels: {device['maxOutputChannels']}")
        print(f"Default Sample Rate: {device['defaultSampleRate']} Hz")
        print("-" * 40)
    
    p.terminate()

list_audio_devices()

# Testa os primeiros 5 índices de câmera
for index in range(5):
    cap = cv2.VideoCapture(index)
    if cap.isOpened():
        print(f"Câmera encontrada no índice {index}")
        ret, frame = cap.read()
        if ret:
            print(f"Frame capturado do índice {index}")
            cv2.imshow("Frame", frame)
            cv2.waitKey(0)
        else:
            print(f"Falha ao capturar o frame do índice {index}")
        cap.release()
    else:
        print(f"Sem câmera no índice {index}")

cv2.destroyAllWindows()
