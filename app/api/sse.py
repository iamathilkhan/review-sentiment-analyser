import time
import json
from flask import Blueprint, Response, stream_with_context, request, abort
from ..core.extensions import redis_client
from ..core.auth_decorators import decode_token
from ..models.user import User

sse_bp = Blueprint('sse', __name__)

@sse_bp.route('/review/<uuid:review_id>')
def review_events(review_id):
    """
    SSE endpoint to track review processing progress.
    Expects JWT token in query param for auth.
    """
    token = request.args.get('token')
    if not token:
        abort(401, description="Authentication token required")
    
    payload = decode_token(token)
    if not payload:
        abort(401, description="Invalid token")

    def event_stream():
        start_time = time.time()
        redis_key = f"review:{review_id}:result"
        
        while True:
            # Check for timeout (120s)
            if time.time() - start_time > 120:
                yield f"data: {json.dumps({'status': 'timeout', 'error': 'Processing timed out'})}\n\n"
                yield "event: close\ndata: timeout\n\n"
                break
                
            # Poll Redis
            cached_result = redis_client.get(redis_key)
            if cached_result:
                result_data = json.loads(cached_result)
                yield f"data: {cached_result.decode('utf-8')}\n\n"
                
                if result_data.get('status') in ['done', 'failed']:
                    yield "event: close\ndata: done\n\n"
                    break
            else:
                # If not in Redis yet, send status "pending" or "processing"
                # For simplicity, we just send a heartbeat or standard poll status
                yield f"data: {json.dumps({'status': 'processing'})}\n\n"
            
            time.sleep(1.5)

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")
