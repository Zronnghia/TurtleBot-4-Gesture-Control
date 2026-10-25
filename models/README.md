# Model MediaPipe Gesture Recognizer

`gesture_recognizer.task` – model chính thức của Google MediaPipe (bản float16, 8 373 440 byte,
SHA256 `97952348cf6a6a4915c2ea1496b4b37ebabc50cbbf80571435643c455f2b0482`), giấy phép Apache 2.0.

Gồm 3 mô hình nối tiếp: phát hiện lòng bàn tay → 21 landmark bàn tay → phân loại 7 cử chỉ
(`Closed_Fist, Open_Palm, Pointing_Up, Thumb_Down, Thumb_Up, Victory, ILoveYou`) + `None`.

Nguồn gốc / tải lại:
`https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task`
(xem https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer).
Thiếu file này thì `gesture_recognition_node.py` tự tải về `~/.cache/tb4_lab04/models/`.
