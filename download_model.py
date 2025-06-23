from sentence_transformers import SentenceTransformer
import os

def download_model():
    """
    Downloads the sentence-transformer model and saves it to the models directory.
    """
    model_name = 'all-MiniLM-L6-v2'
    save_path = f'./models/{model_name}'

    print(f"Checking if model '{model_name}' exists at '{save_path}'...")

    if os.path.exists(save_path) and os.listdir(save_path):
        print("Model already exists and is not empty. Skipping download.")
        return

    print("Model not found or directory is empty. Downloading model...")
    
    try:
        model = SentenceTransformer(model_name)
        print(f"Saving model to '{save_path}'...")
        model.save(save_path)
        print("Model downloaded and saved successfully!")
    except Exception as e:
        print(f"An error occurred during model download: {e}")

if __name__ == "__main__":
    download_model() 