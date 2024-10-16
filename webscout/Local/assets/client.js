marked.setOptions({
    pedantic: false,
    gfm: true,
    breaks: true
});

document.body.height = window.innerHeight;

let isGenerating = false;

const GlobalEncoder = new TextEncoder;
const GlobalDecoder = new TextDecoder;
const maxLengthInput = 100000; // one hundred thousand characters

function bytesToBase64(bytes) {
    let binaryString = '';
    for (let i = 0; i < bytes.length; i++) {
        binaryString += String.fromCharCode(bytes[i]);
    }
    return btoa(binaryString);
}

function base64ToBytes(base64) {
    const binString = atob(base64);
    const bytes = new Uint8Array(binString.length);
    for (let i = 0; i < binString.length; i++) {
        bytes[i] = binString.charCodeAt(i);
    }
    return bytes;
}

function fixBase64Padding(base64) {
    let _base64_no_equals = base64.replace(/=/g, '');
    const missingPadding = _base64_no_equals.length % 4;
    if (missingPadding) {
        _base64_no_equals += '='.repeat(4 - missingPadding);
    }
    return _base64_no_equals;
}

function encode(text) {
    let bytes = GlobalEncoder.encode(text);
    return bytesToBase64(bytes);
}

function decode(base64) {
    let bytes = base64ToBytes(base64);
    return GlobalDecoder.decode(bytes);
}

const conversationWindow = document.getElementById('conversationWindow');
const resetButton = document.getElementById('resetButton');
const removeButton = document.getElementById('removeButton');
const submitButton = document.getElementById('submitButton');
const newBotMessageButton = document.getElementById('newBotMessageButton');
const swipeButton = document.getElementById('swipeButton');
const inputBox = document.getElementById('inputBox');
const uploadButton = document.getElementById('fileUploadButton');
const uploadForm = document.getElementById('fileInput');
const summarizeButton = document.getElementById('summarizeButton');
const darkModeToggle = document.getElementById('darkModeToggle');

function popAlertPleaseReport(text) {
    alert(
        text + "\n\nPlease report this issue to the developer at this link:\n" +
        "https://github.com/OE-LUCIFER/Webscout"
    );
}

function handleError(message) {
    if (!strHasContent(message)) {
        console.error('An error occurred, but no error message was provided');
        return;
    } else {
        console.error('An error occurred:', message);
        return;
    }
}

function setIsGeneratingState(targetState) {
    if (isGenerating === targetState) { return; }

    if (targetState) {
        submitButton.textContent = '🚫 Cancel';
        submitButton.classList.add('cancel-button');
        resetButton.textContent = '🔄 Cancel and Restart';
        removeButton.disabled = true;
        newBotMessageButton.disabled = true;
        swipeButton.textContent = '🔀 Cancel and Re-roll';
        summarizeButton.disabled = true;
    } else {
        submitButton.textContent = '📤 Send';
        submitButton.classList.remove('cancel-button');
        resetButton.textContent = '🔄 Restart Chat';
        removeButton.disabled = false;
        newBotMessageButton.disabled = false;
        swipeButton.textContent = '🔀 Re-roll Last Message';
        summarizeButton.disabled = false;
    }

    isGenerating = targetState;
    console.log('Set generating state:', targetState);
}

function getMostRecentMessage() { 
    return conversationWindow.firstChild;
}

function appendNewMessage(message) {
    let mostRecentMessage = getMostRecentMessage();
    if (mostRecentMessage !== null) {
        conversationWindow.insertBefore(message, mostRecentMessage);
    } else {
        conversationWindow.append(message);
    }
}

function createMessage(role, content) {
    const message = document.createElement('div');
    message.className = `message ${role}-message`;
    
    const emoji = role === 'user' ? '👤' : '🤖';
    message.innerHTML = `<span class="emoji">${emoji}</span> ${marked.parse(content)}`;
    
    highlightMessage(message);
    return message;
}

function highlightMessage(message) {
    message.querySelectorAll('pre code').forEach(block => {
        hljs.highlightElement(block);
        addCopyButton(block);
    });
}

function addCopyButton(block) {
    const button = document.createElement('button');
    button.textContent = 'Copy';
    button.className = 'copy-code-btn';
    button.addEventListener('click', () => {
        navigator.clipboard.writeText(block.textContent).then(() => {
            button.textContent = 'Copied!';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        });
    });
    block.parentNode.insertBefore(button, block);
}

function removeLastMessage() {
    return new Promise((resolve, reject) => {
        const lastMessage = getMostRecentMessage();

        if (lastMessage === null) {
            resolve();
            return;
        }

        fetch('/remove', {
            method: 'POST',
        })
        .then(response => {
            if (response.ok) {
                lastMessage.remove();
                console.log('removeLastMessage: removed node');
                updatePlaceholderText();
                resolve();
            } else {
                handleError(
                    'Bad response from /remove: ' +
                    response.status +
                    response.statusText
                );
                reject();
            }
        })
        .catch(error => {
            handleError("removeLastMessage: " + error.message);
            reject();
        });
    });
}

function strHasContent(str) {
    return str && str !== '';
}

function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            resolve(e.target.result);
        };
        reader.onerror = function(e) {
            reject(e);
        };
        reader.readAsText(file);
    });
}

function streamToMessage(reader, targetMessage, prefix) {
    let accumulatedText = prefix || '';
    let accumulatedBase64 = '';

    return new Promise((resolve, reject) => {
        function processStream({ done, value }) {
            if (done) {
                if (accumulatedBase64.length > 0) {
                    try {
                        accumulatedText += decode(
                            fixBase64Padding(accumulatedBase64)
                        );
                    } catch (error) {
                        handleError(
                            "Cannot decode remainder of base64: " +
                            accumulatedBase64
                        );
                    }
                }
                resolve();
                return;
            }

            let chunk = GlobalDecoder.decode(value);
            accumulatedBase64 += chunk;

            let chunks = accumulatedBase64.split('\n');
            accumulatedBase64 = chunks.pop();

            for (const base64Chunk of chunks) {
                if (base64Chunk) {
                    try {
                        decoded_chunk = decode(fixBase64Padding(base64Chunk));
                        accumulatedText += decoded_chunk;
                    } catch (error) {
                        handleError(
                            "Decoding base64 chunk: " + error.name + " -- " +
                            error.message + " : " + base64Chunk
                        );
                    }
                }
            }

            targetMessage.innerHTML = marked.parse(accumulatedText);
            highlightMessage(targetMessage);

            reader.read().then(processStream);
        }

        reader.read().then(processStream);
    });
}

async function submitForm(event) {
    event.preventDefault();
    const prompt = inputBox.value.trim();

    if (isGenerating) {
        await cancelGeneration();
        return;
    }

    if (!prompt) {
        newBotMessage();
        updatePlaceholderText();
        return;
    }

    if (prompt.length > maxLengthInput) {
        alert('Input exceeds maximum length of 100k characters');
        return;
    }

    setIsGeneratingState(true);
    showLoading();

    let userMessage = createMessage('user', prompt);
    highlightMessage(userMessage);
    appendNewMessage(userMessage);

    inputBox.value = '';
    autoResizeTextarea(inputBox);

    try {
        const response = await fetch('/submit', {
            method: 'POST',
            body: encode(prompt)
        });

        hideLoading();
        const botMessage = createMessage('bot', '');
        appendNewMessage(botMessage);

        const reader = response.body.getReader();
        await streamToMessage(reader, botMessage, null);

    } catch (error) {
        console.error('Error:', error);
        hideLoading();
    } finally {
        setIsGeneratingState(false);
        updatePlaceholderText();
    }
}

function updatePlaceholderText() {
    if (isGenerating) {
        console.log('refuse to fetch context string - currently generating');
        return;
    }

    return fetch('/get_context_string')
        .then(response => response.json())
        .then(data => {
            inputBox.placeholder = decode(data.text);
        })
        .catch(error => {
            handleError('updatePlaceholderText: ' + error.message);
        });
}

function cancelGeneration() {
    return new Promise((resolve, reject) => {
        if (!isGenerating) {
            resolve();
            return;
        }

        fetch('/cancel', {
            method: 'POST'
        })
        .then(response => {
            if (response.ok) {
                setIsGeneratingState(false);
                const lastMessage = getMostRecentMessage();
                if (lastMessage === null) {
                    resolve();
                } else {
                    lastMessage.remove();
                    resolve();
                }
            } else {
                handleError(
                    "cancelGeneration: bad response from /cancel: " +
                    response.status +
                    response.statusText
                );
                reject();
            }
        })
        .catch(error => {
            handleError('cancelGeneration: ' + error.message);
            reject();
        });
    });
}

function newBotMessage() {
    return new Promise((resolve, reject) => {
        if (isGenerating) {
            console.log('refuse to trigger newBotMessage - already generating');
            resolve();
            return;
        }

        let v = inputBox.value;
        let encodedPrefix = null;
        let botMessage = null;

        if (strHasContent(v)) {
            if (v.length > maxLengthInput) {
                alert(
                    'length of input exceeds maximum allowed length of ' +
                    '100k characters'
                );
                resolve();
                return;
            }

            encodedPrefix = encode(v);
            accumulatedText = v;

            botMessage = createMessage('bot', v);
            highlightMessage(botMessage);
            appendNewMessage(botMessage);
            inputBox.value = '';
        }

        setIsGeneratingState(true);

        fetch('/trigger', { method: 'POST', body: encodedPrefix })
        .then(response => {
            if (response.ok) {
                if (botMessage === null) {
                    botMessage = createMessage('bot', '');
                    appendNewMessage(botMessage);
                }

                inputBox.value = '';

                return streamToMessage(
                    response.body.getReader(), botMessage, v
                );
            } else {
                handleError(
                    "Bad response from /trigger: " +
                    response.status +
                    response.statusText
                );
                reject();
            }
        })
        .then(() => {
            setIsGeneratingState(false);
            updatePlaceholderText();
            resolve();
        })
        .catch(error => {
            handleError("newBotMessage: " + error.message);
            setIsGeneratingState(false);
            updatePlaceholderText();
            reject();
        });
    });
}

function resetConversation() {
    fetch('/reset', { method : 'POST' })
    .then(response => {
        if (response.ok) {
            conversationWindow.innerHTML = '';
            updatePlaceholderText();
        } else {
            handleError(
                "Bad response from /reset: " +
                response.status +
                response.statusText
            );
        }
    })
    .catch(error => {
        handleError("resetConversation: " + error.message);
    });
}

function populateConversation() {
    fetch('/convo', { method : "GET" })
    .then(response => {
        if (!response.ok) {
            handleError(
                "Bad response from /convo: " +
                response.status + 
                response.statusText
            );
            return;
        } else {
            updatePlaceholderText();
            return response.json();
        }
    })
    .then(data => {
        let msgs = Object.keys(data);
        conversationWindow.innerHTML = '';

        for (let i = 0; i < msgs.length; i++) {
            const msgKey = msgs[i];
            const msg = data[msgKey];
            let keys = Object.keys(msg);

            let role = decode(keys[0]);
            let content = decode(msg[keys[0]]);

            if (role != 'system') {
                let newMessage = createMessage(role, content);
                highlightMessage(newMessage);
                appendNewMessage(newMessage);
            }
        }
    })
    .catch(error => {
        handleError("populateConversation: " + error.message);
    });
}

async function swipe() {
    if (isGenerating) {
        await cancelGeneration();
        setTimeout(newBotMessage, 500);
        await updatePlaceholderText();
    } else {
        await removeLastMessage();
        setTimeout(newBotMessage, 500);
        await updatePlaceholderText();
    }
}

function generateSummary() {
    return new Promise((resolve, reject) => {
        if (isGenerating) {
            console.log('refuse to generate summary - already generating');
            resolve();
            return;
        }

        setIsGeneratingState(true);

        fetch('/summarize', { method : 'GET' })
        .then(response => {
            if (response.ok) {
                return response.text();
            } else {
                setIsGeneratingState(false);
                handleError(
                    "Bad response from /summarize: " +
                    response.status +
                    response.statusText
                );
                reject();
            }
        })
        .then(data => {
            let summary = decode(data);
            console.log('summary:', summary);
            alert(summary);
            setIsGeneratingState(false);
            resolve();
        })
        .catch(error => {
            handleError("generateSummary: " + error.message);
            setIsGeneratingState(false);
            reject();
        });
    });
}

function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

function showLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message bot-message loading';
    loadingDiv.innerHTML = '<span class="emoji">⏳</span> Thinking...';
    conversationWindow.prepend(loadingDiv);
}

function hideLoading() {
    const loadingDiv = document.querySelector('.loading');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
    updateDarkModeButton();
}

function updateDarkModeButton() {
    const isDarkMode = document.body.classList.contains('dark-mode');
    darkModeToggle.innerHTML = isDarkMode ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
}

document.addEventListener('DOMContentLoaded', function() {
    populateConversation();

    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
    updateDarkModeButton();

    inputBox.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            submitForm(event);
        }
    });

    inputBox.addEventListener('input', function() {
        autoResizeTextarea(this);
    });

    submitButton.addEventListener('click', submitForm);
    removeButton.addEventListener('click', removeLastMessage);
    resetButton.addEventListener('click', function() {
        if (isGenerating) {
            cancelGeneration();
            resetConversation();
        } else {
            resetConversation();
        }
    });
    newBotMessageButton.addEventListener('click', newBotMessage);
    swipeButton.addEventListener('click', swipe);
    uploadButton.addEventListener('click', function() {
        uploadForm.click();
    });

    uploadForm.addEventListener('change', async function(event) {
        const files = event.target.files;
        if (files.length > 0) {
            try {
                for (const file of files) {
                    const content = await readFileAsText(file);
                    inputBox.value += "```\n" + content + "\n```\n\n";
                }
                inputBox.scrollTop = inputBox.scrollHeight;
                inputBox.selectionStart = inputBox.value.length;
                inputBox.selectionEnd = inputBox.value.length;
                autoResizeTextarea(inputBox);
            } catch (error) {
                handleError("uploadForm: event change: " + error.message);
            }
        }
    });

    summarizeButton.addEventListener('click', generateSummary);
    darkModeToggle.addEventListener('click', toggleDarkMode);
});

window.onresize = function() { 
    document.body.height = window.innerHeight;
}