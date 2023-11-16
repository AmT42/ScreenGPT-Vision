# GPT Vision Chat – A Friendly Desktop Companion

## Hey there, fellow explorers of GPT! 🚀

I've put together a little side project called **GPT Vision Chat**. Think of it as a casual chat with GPT-4, but from the comfort of your desktop and with a cool twist: the ability to throw in images! Yep, now asking questions about those pesky screenshots or any visual puzzles is just a click or a hotkey away.

## What's This All About? 🤔

Ever been knee-deep in work and stumbled upon an error message as cryptic as an ancient manuscript? Or maybe you've had a math equation staring at you from a photo, begging to be solved. Instead of tab-hopping and website navigating, why not just press a key, snag a screenshot, and get querying? That's the convenience GPT Vision Chat brings to your desktop!

## Features (The Cool Bits) 🎉

- **Chat with GPT-4**: Just type in your question and voilà – wisdom from GPT-4.
- **Screenshot Magic**: Capture your screen's content and let GPT-4 do the heavy lifting.
- **Lazy Loading**: Queue up those screenshots and fire away all your queries at once.
- **Shortcut Simplicity**: Hit Ctrl+P and your screenshot is ready to be analyzed.
- **Feather-Light**: A minimalist app that's easy on your machine.

## The Backstory 📚

Cobbled together in just 3 days, this app is my humble foray into desktop development – no prior experience, just a lot of googling and some help from my code mentor, [Code Mentor GPT](https://chat.openai.com/g/g-zdGAIuWTl-code-mentor) (he even helped with the editing this README). The code might be rough around the edges, and the UI won't win beauty contests, but it gets the job done. If this little tool piques your interest, I'm all in for round two of development. Think object localization, automated actions... the sky's the limit!

## Join the Fun! 🎈

Stumble upon this repo and find it neat? Star it, fork it, send pull requests, or just spread the good word – every bit of support counts. Your interest is the fuel for this project's growth. Let's make desktop AI chat a thing!

## How to Get It Rolling 🛠️

### Prerequisites

- Python 3.8+
- OpenAI API key (Don't have one? No worries! Head over to [OpenAI's API keys page](https://platform.openai.com/api-keys) to get your key.)
- Docker (optional, for Docker setup)

### Installation

#### Clone the Repository
   ```bash
   git clone https://github.com/AmT42/ScreenGPT-Vision.git
   cd ScreenGPT-Vision
   ```
#### Create a .env File
Inside the ScreenGPT-Vision directory, create a file named .env. 
**Unix-based systems (Linux, macOS, etc.)**
   ```bash
   touch .env
   ```
**Windows**
  ```bash
   type nul > .env
   ```
#### Add Your API Key to the .env File
Open your new .env file with your favorite text editor and add the following line:
OPEN_API_KEY=your-openai-key

#### With Docker  
1. **Run docker compose**
   ```bash
   docker-compose up --build
   ```
#### Run the Frontend
1. Install PyQT5 to run the front
    ```bash
    pip install PyQt5==5.15.10
    ```
2. In a separate terminal, execute the following command:
    ```bash
    python GUI/app.py
    ```


#### Without Docker  
1. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the Backend**
   ```bash
   uvicorn app.main:app --reload
   ```

#### Run the Frontend
In a separate terminal, execute the following command:
```bash
 python GUI/app.py
 ```
## Usage

[Include instructions on how to use the application, along with any screenshots or videos if available.]

## Want to Contribute? 🤝

If you've got ideas or code to improve this app, I'm all ears! Contributing is simple:

1. Fork this repo.
2. Create a branch for your awesome new feature (`git checkout -b amazing-feature`).
3. Commit your changes (`git commit -m 'Add some awesomeness'`).
4. Push to the branch (`git push origin amazing-feature`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation 📄

If you end up using GPT Vision Chat in your work, a shoutout would be super cool:

```bibtex
  @misc{ScreenGPT-Vision,
    author = "AmT42",
    title = "GPT Vision Chat for Desktop",
    year = "2023",
    url = "https://github.com/AmT42/ScreenGPT-Vision"
  }
  ```

## Contact

AmT42 - ahmet_celebi@hotmail.fr / https://www.linkedin.com/in/ahmet-celebi-973b63197/


Project Link: https://github.com/AmT42/ScreenGPT-Vision

    
=======
    
