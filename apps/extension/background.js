// Background service worker

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && tab.url.includes('instagram.com')) {
    // Inject content script when page is ready
    chrome.tabs.sendMessage(tabId, { action: 'capture' }).catch(() => {
      // Content script might not be ready yet
    });
  }
});
