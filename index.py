from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <h1>Source2Social - Test Deploy</h1>
    <p>If you can see this, the Vercel deployment is working!</p>
    <p>Main app should be loaded next...</p>
    '''

@app.route('/health')
def health():
    return {"status": "ok", "message": "Basic Flask app working"}

# For Vercel
if __name__ == '__main__':
    app.run()