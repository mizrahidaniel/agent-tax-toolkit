"""Encryption utilities for sensitive data (TINs)."""

import os
from cryptography.fernet import Fernet


class TINEncryption:
    """Handle encryption/decryption of Tax Identification Numbers."""

    def __init__(self, key: bytes | None = None):
        """Initialize with encryption key.
        
        Args:
            key: 32-byte key (Fernet format). If None, generates new key.
        """
        if key is None:
            key = Fernet.generate_key()
        self.cipher = Fernet(key)
        self.key = key

    @classmethod
    def from_env(cls) -> "TINEncryption":
        """Load encryption key from TIN_ENCRYPTION_KEY environment variable."""
        key = os.getenv("TIN_ENCRYPTION_KEY")
        if not key:
            raise ValueError(
                "TIN_ENCRYPTION_KEY not set. Generate with: python -c "
                "'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        return cls(key.encode())

    def encrypt(self, tin: str) -> bytes:
        """Encrypt a TIN.
        
        Args:
            tin: Tax ID Number (e.g., "123-45-6789" or "12-3456789")
            
        Returns:
            Encrypted TIN bytes
        """
        # Remove dashes/spaces
        tin_clean = tin.replace("-", "").replace(" ", "")
        return self.cipher.encrypt(tin_clean.encode())

    def decrypt(self, encrypted_tin: bytes) -> str:
        """Decrypt a TIN.
        
        Args:
            encrypted_tin: Encrypted TIN bytes
            
        Returns:
            Decrypted TIN (no formatting)
        """
        return self.cipher.decrypt(encrypted_tin).decode()

    def format_tin(self, tin: str, type: str = "ssn") -> str:
        """Format TIN with dashes.
        
        Args:
            tin: Unformatted TIN
            type: "ssn" (XXX-XX-XXXX) or "ein" (XX-XXXXXXX)
            
        Returns:
            Formatted TIN
        """
        tin_clean = tin.replace("-", "").replace(" ", "")
        
        if type == "ssn" and len(tin_clean) == 9:
            return f"{tin_clean[:3]}-{tin_clean[3:5]}-{tin_clean[5:]}"
        elif type == "ein" and len(tin_clean) == 9:
            return f"{tin_clean[:2]}-{tin_clean[2:]}"
        else:
            return tin_clean
