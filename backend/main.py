from fastapi import FastAPI 
app = FastAPI() 
@app.get("/") 
def read_root(): 
    return {"message": "Nutri-App Backend con Python y FastAPI funcionando"} 
