import streamlit as st
import os
import tempfile
# Updated imports for PyPDFLoader and TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import TextLoader
from langchain_google_community import GoogleDriveLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import traceback
from google.oauth2 import service_account

# Load environment variables from .env file if present (good practice)
load_dotenv()

# --- Page Configuration (Main App) ---
st.set_page_config(
    page_title="Cerebro AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📚 Cerebro AI Assistant")
st.write("Welcome! Use the sidebar to upload documents, load from Google Drive, chat with them using RAG, generate flashcards, or create MC questions.")


# --- Initialize Session State ---
# (Keep existing session state initializations)
if "deepseek_api_key" not in st.session_state: st.session_state.deepseek_api_key = None
if "deepseek_base_url" not in st.session_state: st.session_state.deepseek_base_url = None
if "processed_text" not in st.session_state: st.session_state.processed_text = None
if "text_chunks" not in st.session_state: st.session_state.text_chunks = None
if "vector_store" not in st.session_state: st.session_state.vector_store = None
if "rag_ready" not in st.session_state: st.session_state.rag_ready = False
if "flashcards_ready" not in st.session_state: st.session_state.flashcards_ready = False
if "gdrive_folder_id" not in st.session_state: st.session_state.gdrive_folder_id = ""
if "gdrive_docs_loaded" not in st.session_state: st.session_state.gdrive_docs_loaded = False
if "gdrive_loaded_text" not in st.session_state: st.session_state.gdrive_loaded_text = ""
SERVICE_ACCOUNT_KEY_FILE = "service_account.json"


# --- Load DeepSeek Credentials from Environment Variables ---
st.session_state.deepseek_api_key = st.secrets["DS_key"]
# Provide a default URL if the env var is not set, but prioritize the env var
default_deepseek_base_url = "https://api.deepseek.com/v1"
st.session_state.deepseek_base_url = os.getenv("deepseek_base_url", default_deepseek_base_url)

# --- Display Credential Status (Sidebar) ---
st.sidebar.header("API Configuration Status")
if st.session_state.deepseek_api_key and st.session_state.deepseek_base_url:
    st.sidebar.success("DeepSeek Chat credentials loaded from environment variables.")
    st.sidebar.caption(f"Using Base URL: {st.session_state.deepseek_base_url}")
else:
    missing_vars = []
    if not st.session_state.deepseek_api_key: missing_vars.append("`deepseek_api_key`")
    if not st.session_state.deepseek_base_url: missing_vars.append("`deepseek_base_url`")
    st.sidebar.error(f"Missing environment variable(s): {', '.join(missing_vars)}.")
    st.warning("Chat/Generation features require DeepSeek credentials set as environment variables.")

# Store chat model name in session state
st.session_state.chat_model = "deepseek-chat" # Assuming default


# --- Google Drive Integration (Sidebar) ---
st.sidebar.header("Google Drive Import (Service Account)")
st.session_state.gdrive_folder_id = st.sidebar.text_input(
    "Google Drive Folder ID:",
    value=st.session_state.gdrive_folder_id,
    placeholder="Enter the ID from the folder URL",
    help=f"Find the Folder ID in the URL. Ensure '{SERVICE_ACCOUNT_KEY_FILE}' is in the app's root directory and the folder is shared with the service account email."
)

# Updated function to use Service Account Key
def load_from_google_drive(folder_id):
    """Loads documents from Google Drive folder using a Service Account."""
    # (Keep existing GDrive loading logic)
    if not folder_id:
        st.sidebar.warning("Please enter a Google Drive Folder ID.")
        return None
    if not os.path.exists(SERVICE_ACCOUNT_KEY_FILE):
         st.sidebar.error(f"`{SERVICE_ACCOUNT_KEY_FILE}` not found.")
         st.sidebar.info("Download Service Account key and place it here. Share Drive folder with service account email.")
         return None
    try:
        st.sidebar.info(f"Loading from GDrive Folder: {folder_id} (Service Account)")
        credentials = service_account.Credentials.from_service_account_file(
            os.path.join(os.path.dirname(__file__), "service_account.json"),
            scopes=['https://www.googleapis.com/auth/drive']
        )
        loader = GoogleDriveLoader(
            folder_id=folder_id,
            credentials=credentials,
            recursive=False
        )
        docs = loader.load()
        if not docs:
            st.sidebar.warning("No documents found/loaded. Check Folder ID & sharing.")
            return ""
        st.sidebar.success(f"Loaded {len(docs)} document(s) from Google Drive.")
        full_text = "\n\n".join([doc.page_content for doc in docs])
        return full_text
    except Exception as e:
        st.sidebar.error(f"Google Drive loading error: {e}")
        st.sidebar.code(traceback.format_exc())
        if "fileNotFound" in str(e): st.sidebar.warning("Folder not found or not shared.")
        elif "invalid_grant" in str(e).lower(): st.sidebar.error("Auth error: Invalid grant.")
        return None

if st.sidebar.button("Load Files from Google Drive", key="load_gdrive_btn"):
     loaded_text = load_from_google_drive(st.session_state.gdrive_folder_id)
     if loaded_text is not None:
         st.session_state.gdrive_loaded_text = loaded_text
         st.session_state.gdrive_docs_loaded = bool(loaded_text)
         if not loaded_text: st.sidebar.info("No text content loaded from Google Drive.")
     else:
         st.session_state.gdrive_docs_loaded = False


# --- Document Processing Functions ---
def get_document_text_from_uploads(files):
    """Loads text from manually uploaded files."""
    # Uses the updated imports for PyPDFLoader and TextLoader
    full_text = ""
    temp_dir = tempfile.mkdtemp()
    processed_files = []
    skipped_files = []
    try:
        for file in files:
            file_path = os.path.join(temp_dir, file.name)
            with open(file_path, "wb") as f: f.write(file.getvalue())
            try:
                if file.type == "application/pdf": loader = PyPDFLoader(file_path) # Uses updated import
                elif file.type == "text/plain": loader = TextLoader(file_path) # Uses updated import
                else:
                    skipped_files.append(f"{file.name} (Unsupported type: {file.type})")
                    continue
                documents = loader.load()
                file_text = "\n\n".join([doc.page_content for doc in documents])
                full_text += f"\n\n--- Uploaded Document: {file.name} ---\n\n" + file_text
                processed_files.append(file.name)
            except Exception as load_error: st.sidebar.warning(f"Could not process {file.name}: {load_error}")
    except Exception as e: st.sidebar.error(f"Error during file handling: {e}")
    finally:
        try:
            for item in os.listdir(temp_dir): os.remove(os.path.join(temp_dir, item))
            os.rmdir(temp_dir)
        except Exception as cleanup_error: st.sidebar.warning(f"Cleanup error: {cleanup_error}")

    if processed_files: st.sidebar.write("Processed Uploads:")
    for name in processed_files: st.sidebar.caption(f"- {name}")
    if skipped_files: st.sidebar.write("Skipped Uploads:")
    for name in skipped_files: st.sidebar.caption(f"- {name}")

    return full_text.strip() if full_text else ""

def get_text_chunks_from_text(text):
    """Splits text into chunks."""
    if not text: return None
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    """Creates a FAISS vector store using BGE embeddings."""
    if not text_chunks: return None
    model_name = "BAAI/bge-base-en-v1.5"
    st.sidebar.caption(f"Using Embedding Model: {model_name} (running locally)")
    try:
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
        st.sidebar.info(f"Loading embedding model '{model_name}' locally...")
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
        st.sidebar.info("Embedding model loaded.")
        return vector_store
    except ImportError:
         st.error("Libraries missing for HuggingFace Embeddings. Please run: pip install langchain-huggingface sentence-transformers")
         return None
    except Exception as e:
        st.sidebar.error(f"Vector Store Error (BGE): {e}")
        st.sidebar.code(traceback.format_exc())
        return None

# --- Sidebar: File Upload and Processing ---
st.sidebar.header("Manual Document Upload")
uploaded_files = st.sidebar.file_uploader(
    "Upload PDF or TXT files", type=["pdf", "txt"], accept_multiple_files=True, key="file_uploader"
)

# Combined Processing Button
st.sidebar.markdown("---")
if st.sidebar.button("Process All Loaded Files", key="process_button"):
    upload_text = get_document_text_from_uploads(uploaded_files) if uploaded_files else ""
    gdrive_text = st.session_state.gdrive_loaded_text
    combined_text = (upload_text + "\n\n" + gdrive_text).strip()
    if not combined_text:
         st.sidebar.warning("No text content found from uploads or Google Drive to process.")
    else:
        with st.spinner("Processing combined text..."):
            st.session_state.processed_text = None
            st.session_state.text_chunks = None
            st.session_state.vector_store = None
            st.session_state.rag_ready = False
            st.session_state.flashcards_ready = False
            st.session_state.pop('flashcards', None)
            st.session_state.pop('mcqs', None)
            st.session_state.processed_text = combined_text
            st.session_state.flashcards_ready = True
            st.sidebar.success("Combined text available for generation.")
            chunks = get_text_chunks_from_text(combined_text)
            if chunks:
                st.session_state.text_chunks = chunks
                vs = get_vector_store(chunks)
                if vs:
                    st.session_state.vector_store = vs
                    st.session_state.rag_ready = True
                    st.sidebar.success("Vector store created using local BGE model.")
                else:
                    st.sidebar.error("Failed to create vector store.")
            else:
                st.sidebar.warning("Could not split combined text into chunks.")

# --- Main Page Content ---
st.markdown("---")
st.header("Instructions")
st.markdown(f"""
1.  **Configure Chat API:** Set `deepseek_api_key` and `deepseek_base_url` as environment variables (lowercase). These are used for Chat/Flashcard/MCQ generation.
2.  **Install Dependencies:** Ensure `pip install -r requirements.txt` is run.
3.  **Google Drive Setup (Optional - Service Account):**
    *   Download a `{SERVICE_ACCOUNT_KEY_FILE}` key file from Google Cloud Console.
    *   Place it in the same directory as this script (`Home_Page.py`).
    *   Share the Google Drive folder with the service account's email address.
    *   Enter the Google Drive Folder ID in the sidebar & click "Load Files from Google Drive".
4.  **Manual Upload (Optional):** Upload PDF/TXT files using the sidebar.
5.  **Process Files:** Click "Process All Loaded Files". This combines text and generates local embeddings.
6.  **Navigate:** Use the sidebar navigation to switch between Cerebro Chat, Flashcards, and MC Questions.
""")

# Button for clearing processed data 
if st.sidebar.button("Clear Processed Data", key="clear_data"):
    st.session_state.processed_text = None
    st.session_state.text_chunks = None
    st.session_state.vector_store = None
    st.session_state.rag_ready = False
    st.session_state.flashcards_ready = False
    st.session_state.gdrive_loaded_text = ""
    st.session_state.gdrive_docs_loaded = False
    st.session_state.pop('flashcards', None)
    st.session_state.pop('current_card_index', None)
    st.session_state.pop('show_answer', None)
    st.session_state.pop('starred_cards', None)
    st.session_state.pop('mcqs', None)
    st.session_state.pop('current_mcq_index', None)
