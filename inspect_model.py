import torch
model = torch.load('cnn_lstm_fast_final_model.pt', map_location='cpu')
for k, v in model.items():
    print(k, v.shape)
