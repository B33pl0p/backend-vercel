import clip
import torch
from PIL import Image
import numpy

#initialization of CLIP
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def extract_text_embedding(query_text):
    with torch.no_grad():
        tokenized_text = clip.tokenize([query_text]).to(device)
        text_embedding = model.encode_text(tokenized_text)
        
        # Check shape and normalization
        #print("Text embedding shape:", text_embedding.shape)
        text_embedding /= text_embedding.norm(dim=1, keepdim=True)
        #print("Normalized text embedding:", text_embedding)

        return text_embedding.cpu().numpy().flatten().astype(numpy.float32)

def extract_image_embedding(image_path):
    """
    Extract image embedding using a pre-trained CLIP model.
    """
    with torch.no_grad():
        # Load and preprocess the image
        image = Image.open(image_path).convert("RGB")
        preprocessed_image = preprocess(image).unsqueeze(0).to(device)
        
        # Get the embedding from the model
        image_embedding = model.encode_image(preprocessed_image)
        
        # Normalize the embedding
        image_embedding /= image_embedding.norm(dim=1, keepdim=True)
        
        # Convert to a 1D NumPy array of floats
        embedding = image_embedding.cpu().numpy().flatten().astype(numpy.float32)
        
        # Debug: Check the shape of the embedding
        print("Embedding shape:", embedding.shape)  # Should be (512,)
        
        return embedding