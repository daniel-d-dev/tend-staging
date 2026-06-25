import os
import torch
import torch.nn as nn
import librosa
import ffmpeg
from transformers import AutoConfig, Wav2Vec2Processor
from transformers.models.wav2vec2.modeling_wav2vec2 import Wav2Vec2Model, Wav2Vec2PreTrainedModel

# the audeering model requires its own custom classes to load correctly. Using HuggingFace's generic AutoModelForAudioClassification mismatches the architecture and loads random weights instead of the trained ones. The below classes were taken from github.com/audeering/w2v2-how-to
class RegressionHead(nn.Module):

    def __init__(self, config):
        super().__init__()
        self.dense = nn.Linear(config.hidden_size, config.hidden_size)
        self.dropout = nn.Dropout(config.final_dropout)
        self.out_proj = nn.Linear(config.hidden_size, config.num_labels)

    def forward(self, features, **kwargs):
        x = features
        x = self.dropout(x)
        x = self.dense(x)
        x = torch.tanh(x)
        x = self.dropout(x)
        x = self.out_proj(x)
        return x


class EmotionModel(Wav2Vec2PreTrainedModel):
    _tied_weights_keys = [] # required by newer versions of transformers. Prevents an attribut error on model loading

    @property
    def all_tied_weights_keys(self): # same fix, newer transformers expects this as a dictionary, not a list
        return {}

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.wav2vec2 = Wav2Vec2Model(config)
        self.classifier = RegressionHead(config)
        self.init_weights()

    def forward(self, input_values):
        outputs = self.wav2vec2(input_values)
        hidden_states = outputs[0]
        hidden_states = torch.mean(hidden_states, dim=1)
        logits = self.classifier(hidden_states)
        return hidden_states, logits


processor = Wav2Vec2Processor.from_pretrained("audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim")
model = EmotionModel.from_pretrained("audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim")
model.eval()


def score_audio(path: str) -> float | None:
    try:
        wav_path = path + ".wav"
        ffmpeg.input(path).output(wav_path, ar = 16000, ac = 1).run(quiet = True, overwrite_output = True) # ar = 16000 sets sample rate to 16kHz, ac = 1 converts to mono. Both required by audeering
        audio, _ = librosa.load(wav_path, sr = 16000, mono = True)
        os.remove(wav_path) # delete the converted wav once loaded. Only the original temp file is cleaned up by the endpoint
        inputs = processor(audio, sampling_rate = 16000, return_tensors = "pt", padding = True)
        with torch.no_grad():
            _, logits = model(inputs["input_values"])
        valence = logits[0][2].item() # audeering outputs three dimensions: arousal (0), dominance (1), valence (2)
        return float(valence)
    except Exception:
        return None