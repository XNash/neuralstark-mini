# NeuralStark Frontend

A React-based frontend for the NeuralStark RAG (Retrieval-Augmented Generation) platform.

## 🪟 Windows Compatibility

This project is optimized for Windows development. The scripts use cross-platform compatible commands.

## Prerequisites

- **Node.js** 16+ (recommended: 18.x or 22.x)
- **Yarn** 1.22+ (recommended package manager)
- **Windows 10/11**, macOS, or Linux

## Quick Start

### Installation

```bash
# Install dependencies
yarn install
```

### Running the Development Server

**On Windows (PowerShell or CMD):**
```bash
yarn start:win
```

**On macOS/Linux:**
```bash
yarn start:unix
```

**Cross-platform (requires cross-env):**
```bash
yarn start
```

**Alternative Windows method:**
```bash
node start-windows.js
```

The app will open at [http://localhost:3000](http://localhost:3000).

## Available Scripts

In the project directory, you can run:

### `yarn start` / `yarn start:win` / `yarn start:unix`

Runs the app in the development mode.

- **Windows**: Use `yarn start:win` or `node start-windows.js`
- **macOS/Linux**: Use `yarn start:unix`
- **Cross-platform**: Use `yarn start` (requires cross-env)

Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `yarn build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `yarn build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

### `yarn test`

Launches the test runner in the interactive watch mode.

## Environment Configuration

Create a `.env` file in the frontend directory:

```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## Windows-Specific Notes

### Path Separators
The project automatically handles Windows path separators (`\`) vs Unix path separators (`/`).

### Command Line
All scripts work in:
- PowerShell
- Command Prompt (CMD)
- Git Bash
- Windows Terminal

### Node Version
Tested with Node.js v22.19.0 on Windows 11.

### Common Issues

**Issue: `basedir=$(dirname ...)` syntax error**
- **Solution**: Use `yarn start:win` instead of calling bash scripts directly

**Issue: Cross-env not found**
- **Solution**: Run `yarn install` to install all dependencies including cross-env

**Issue: Permission denied on node_modules**
- **Solution**: Run your terminal as Administrator or check file permissions

## Backend Connection

The frontend connects to the FastAPI backend at `http://localhost:8001/api`.

Make sure the backend is running before starting the frontend:

```bash
# In the backend directory
pip install -r requirements.txt
python server.py
```

## Features

- 💬 Chat interface with RAG-powered responses
- 📚 Document management and indexing
- ⚙️ Settings configuration
- 🤖 Cerebras AI integration (gpt-oss-120b)
- 🌐 Multilingual support (English/French)
- 📊 Document statistics and cache management

## Technology Stack

- React 19.0
- Tailwind CSS
- Radix UI Components
- React Router
- Axios for API calls
- React Markdown for message rendering

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
