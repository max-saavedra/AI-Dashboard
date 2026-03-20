from supabase import create_client

url = "https://yrenqasaehjoxzzoxqgr.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlyZW5xYXNhZWhqb3h6em94cWdyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5MzQ2ODQsImV4cCI6MjA4OTUxMDY4NH0.0IxgWLT_MB4EnRC81khZv_c2s24l6p7QG3SD0K8RgtA"

supabase = create_client(url, key)

res = supabase.auth.sign_up({
    "email": "test123@example.com",
    "password": "TestPassword123!"
})

print(res)
