from sqlalchemy import Enum

# Questo file serve solo a separare gli enum usati nei modelli

# Stato del documento: uploaded, parsed, failed
document_status_enum = Enum("uploaded", "parsed", "failed", name="document_status")

# Tipo di documento: cv, jd
document_type_enum = Enum("cv", "jd", name="document_type")

# Tipo di ricerca: cv_search, jd_search
search_type_enum = Enum("cv_search", "jd_search", name="search_type")

# Ruolo utente: candidate, recruiter, admin
user_role_enum = Enum("candidate", "recruiter", "admin", name="user_role")
