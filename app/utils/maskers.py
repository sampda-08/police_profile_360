def mask_id_number(val: str) -> str:
    """
    Masks sensitive ID numbers to prevent unauthorized visual exposure.
    Example: '123456789012' becomes 'XXXXXXXX9012'
    """
    if not val:
        return ""
    val_str = str(val).strip()
    if len(val_str) <= 4:
        return "XXXX"
    return "X" * (len(val_str) - 4) + val_str[-4:]
