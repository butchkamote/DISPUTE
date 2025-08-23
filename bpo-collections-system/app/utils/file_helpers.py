import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def save_payment_proofs(files, proof_type):
    """
    Save multiple uploaded proof of payment files and return the file paths
    """
    if not files or not files[0]:
        return []
        
    proofs = []
    uploads_dir = os.path.join(current_app.root_path, '..', 'uploads', 'payment_proofs')
    os.makedirs(uploads_dir, exist_ok=True)
    
    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(uploads_dir, unique_filename)
            file.save(file_path)
            
            # Return the relative path to store in the database
            relative_path = os.path.join('uploads', 'payment_proofs', unique_filename)
            proofs.append({
                'path': relative_path,
                'type': proof_type
            })
            
    return proofs