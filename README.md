# chromaviz

ChromaViz is a lightweight Flask UI and API for managing and visualizing ChromaDB collections. It supports either a local embedded Chroma store or a remote Chroma HTTP server, and can use local Sentence-Transformers or a remote embeddings service.

Container image: ghcr.io/knowusuboaky/chromaviz:latest

Main features:
• Browse collections, see counts, and inspect configuration
• Create, clone, delete collections; add, update, and remove documents
• Run semantic queries with optional metadata and document filters
• Export data to JSON with selectable fields (documents, metadata, embeddings)
• Launch an interactive visualization for any collection

How it works:
• The web UI runs on one port, and the visualizer runs on the next port number (UI on PUBLIC_PORT, visualizer on PUBLIC_PORT + 1).
• By default, the app uses a local persistent Chroma directory inside the container. You can switch to a remote Chroma server by setting the mode to “http” and pointing to its host and port.
• Embeddings can be generated locally by downloading a Sentence-Transformers model into the models cache, or delegated to a remote embeddings HTTP service.

Common settings (environment variables):
• CHROMA_MODE: “persistent” (embedded) or “http” (remote server)
• CHROMA_DB_PATH: data directory for embedded mode
• CHROMA_HTTP_HOST and CHROMA_HTTP_PORT: remote Chroma host and port
• EMBEDDINGS_MODE: “local” or “http”
• EMBEDDING_MODEL and EMBEDDING_MODEL_PATH: local model name and cache path
• PUBLIC_HOST and PUBLIC_PORT: used to build links; visualizer uses PUBLIC_PORT + 1
• CONTINUE_WITHOUT_EMBEDDINGS: run the UI even if embeddings are unavailable

Key endpoints:
• /heartbeat for a quick health check
• /get-collections and /count-collections for collection discovery
• /api/create-new-collection, /api/delete-collection-v2, and /api/delete-all-collections-v2 for lifecycle operations
• /api/add-document, /api/update-document, and /api/delete-document for document management
• /api/query-documents for semantic search
• /gather-export-data and /export-data-to-json for exporting
• /visualize-collection to start the visualizer

Typical workflow:

1. Start the container with a persistent data volume and an optional models cache.
2. Open the UI on the mapped host port to configure settings and manage collections.
3. Import or add documents, then query or visualize them.
4. Export data as needed for downstream tasks.

Notes:
• The app will run without embeddings if requested, allowing you to browse and export data even when model downloads are not possible.
• When using a remote Chroma server, ensure network access between the app and the server.
