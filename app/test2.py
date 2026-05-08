from langchain_community.embeddings import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://134.199.206.176:11434"
)

vector = embeddings.embed_query("Halo dunia")

print(len(vector))