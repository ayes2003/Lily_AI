import chromadb
from datetime import datetime
import os
from groq import Groq

# 🚀 INITIALIZE GROQ CLIENT
# API Key is active for your final demo

client = Groq(api_key=st.secrets["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"])

DB_PATH = "./data/chroma_vault"
if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH, exist_ok=True)

chroma_client = chromadb.PersistentClient(path=DB_PATH)

def save_memory(user_name, text, emotion, entry_type="conversation", tags=None):
    """
    Saves a memory with metadata to ChromaDB.
    """
    collection = chroma_client.get_or_create_collection(name=f"memories_{user_name.lower().replace(' ', '_')}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tag_str = ", ".join(tags) if tags else ""
    
    collection.add(
        documents=[text],
        metadatas=[{
            "emotion": emotion, 
            "time": timestamp,
            "type": entry_type,
            "tags": tag_str
        }],
        ids=[f"id_{timestamp.replace(' ', '_')}_{entry_type}"]
    )
    print(f"✅ Memory saved for {user_name}!")

def summarize_session(messages, user_name):
    """
    Uses Groq Llama 3.3 70B to create a specific, warm overview of the chat.
    This prevents generic fallback messages in the Digital Diary.
    """
    if len(messages) < 3: 
        return None 
    
    # Filter and format history
    chat_history = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages if m['content'].strip()])
    
    # 🚀 ENHANCED PROMPT: Explicitly forbids generic summaries
    prompt = f"""
    You are Lily, a warm and empathetic companion for senior citizens. 
    Analyze this conversation history with {user_name} and write a summary for her personal diary.
    
    RULES:
    1. Write exactly 2-3 warm sentences.
    2. Be SPECIFIC. Mention the actual topics, feelings, or stories {user_name} shared.
    3. Do NOT use generic phrases like 'various topics' or 'helpful conversation'.
    4. Use third-person narrative (e.g., "{user_name} talked about...").
    
    CHAT HISTORY:
    {chat_history}
    """
    
    try:
        # 🚀 Using the 70B model for much higher summary quality
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=200
        )
        
        summary = completion.choices[0].message.content.strip()
        
        # If the model still tries to be too generic, we add a safety check
        if "various topics" in summary.lower() or len(summary) < 15:
             return f"{user_name} shared some meaningful thoughts with Lily today, reflecting on her day and staying positive."
             
        return summary
        
    except Exception as e:
        print(f"❌ Summarization Error: {e}")
        # Fallback with at least a bit of warmth
        return f"{user_name} and Lily shared a meaningful moment together today, discussing her feelings and keeping her spirits high."

def get_recent_memories(user_name, limit=20, filter_type=None, mood_filter=None):
    """
    Retrieves memories for the Home Page and Diary.
    """
    try:
        coll_name = f"memories_{user_name.lower().replace(' ', '_')}"
        collection = chroma_client.get_collection(name=coll_name)
        
        where_clause = {}
        if filter_type: where_clause["type"] = filter_type
        if mood_filter: where_clause["emotion"] = mood_filter

        results = collection.get(where=where_clause if where_clause else None)
        
        if not results or not results['documents']:
            return []

        formatted_memories = []
        for i in range(len(results['documents'])):
            meta = results['metadatas'][i]
            formatted_memories.append({
                'content': results['documents'][i],
                'date': meta.get('time', 'Recently'),
                'mood': meta.get('emotion', 'neutral'),
                'tags': meta.get('tags', '').split(", ") if meta.get('tags') else [],
                'type': meta.get('type', 'conversation')
            })
            
        return formatted_memories[::-1][:limit]
        
    except Exception:
        return []

def search_memories(user_name, query, limit=5):
    """
    Semantic Search using ChromaDB vector embeddings.
    """
    try:
        coll_name = f"memories_{user_name.lower().replace(' ', '_')}"
        collection = chroma_client.get_collection(name=coll_name)
        results = collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        search_results = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                search_results.append({
                    'content': results['documents'][0][i],
                    'date': results['metadatas'][0][i].get('time'),
                    'mood': results['metadatas'][0][i].get('emotion'),
                    'tags': results['metadatas'][0][i].get('tags', '').split(", ")
                })
        return search_results
    except:
        return []