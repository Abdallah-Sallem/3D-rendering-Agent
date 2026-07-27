import socket
import json

def run_in_blender(code_str, host='localhost', port=9876, timeout=60.0):
    payload = json.dumps({
        "type": "execute",
        "code": code_str,
        "strict_json": False
    }) + "\0"
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            s.sendall(payload.encode('utf-8'))
            
            buf = bytearray()
            while True:
                try:
                    chunk = s.recv(16384)
                    if not chunk:
                        break
                    buf.extend(chunk)
                    if b"\0" in buf:
                        break
                except socket.timeout:
                    break
                    
            if buf:
                line, _, _ = bytes(buf).partition(b"\0")
                try:
                    return json.loads(line.decode('utf-8', errors='ignore'))
                except Exception as e:
                    return {"status": "error", "message": f"Decode error: {e}. Raw: {line[:200]}"}
            else:
                return {"status": "error", "message": "No response received"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
