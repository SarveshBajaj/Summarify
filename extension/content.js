// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getVideoUrl') {
    const url = window.location.href;
    sendResponse({ url });
  }
  return true;
});

// Add a button to the YouTube page
function addSummarizeButton() {
  if (window.location.href.includes('youtube.com/watch')) {
    // Check if our button already exists
    if (document.getElementById('summarify-button')) return;
    
    // Find the YouTube controls
    const metaSection = document.querySelector('#above-the-fold #top-row');
    if (!metaSection) {
      // If we can't find the controls, try again later
      setTimeout(addSummarizeButton, 1000);
      return;
    }
    
    // Create our button
    const button = document.createElement('button');
    button.id = 'summarify-button';
    button.innerHTML = 'Summarize Video';
    button.style.cssText = 'background: #cc0000; color: white; border: none; padding: 5px 10px; border-radius: 3px; margin-right: 10px; cursor: pointer; font-family: Roboto, Arial, sans-serif;';
    
    // Add click handler
    button.addEventListener('click', () => {
      chrome.runtime.sendMessage({ 
        action: 'summarize', 
        url: window.location.href 
      });
    });
    
    // Add to page
    metaSection.appendChild(button);
  }
}

// Run when page loads
window.addEventListener('load', addSummarizeButton);

// Also run when navigation happens within YouTube
let lastUrl = location.href; 
new MutationObserver(() => {
  if (location.href !== lastUrl) {
    lastUrl = location.href;
    setTimeout(addSummarizeButton, 1000); // Delay to ensure DOM is ready
  }
}).observe(document, { subtree: true, childList: true });
