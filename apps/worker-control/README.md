# Worker-control beta

This lightweight Cloud Run control plane gates the private Studio, initiates object-scoped resumable Cloud Storage
uploads, validates completed sources, persists production records, serializes independent jobs, and invokes the local
Ampersand engine boundary. It does not contain audio algorithms; native media work remains in `services/media-worker`.

The beta intentionally runs one worker instance and one job at a time. Source objects and completed outputs are durable;
FFmpeg scratch work stays on fast ephemeral storage. Upload session URLs and the beta token must never be logged or
persisted.
