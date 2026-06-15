// Check if current URL is a profile page
function isProfilePage(url) {
  const match = url.match(/instagram\.com\/([^/?]+)\/?$/);
  return match && !['reels', 'explore', 'stories', 'accounts', 'direct'].includes(match[1]);
}

// Capture and send page
async function capturePage() {
  const url = window.location.href;
  console.log('IG Farm: capturePage start', url);
  
  if (!isProfilePage(url)) {
    console.log('IG Farm: Not a profile page');
    return;
  }

  const html = document.documentElement.outerHTML;
  const title = document.title;
  const capturedAt = new Date().toISOString();
  const payload = {
    url,
    html,
    title,
    captured_at: capturedAt,
  };

  console.log('IG Farm: sending capture payload', { url, title, captured_at: capturedAt });

  try {
    const response = await fetch('http://localhost:8001/api/capture', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    console.log('IG Farm: capture response', data);
    
    if (data.status === 'ok' && data.next_profile) {
      const delay = 3000 + Math.random() * 5000;
      console.log('IG Farm: navigating to next profile after', delay, 'ms', data.next_profile);
      setTimeout(() => {
        window.location.href = data.next_profile;
      }, delay);
    }
  } catch (error) {
    console.error('IG Farm: Capture failed', error);
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message && message.action === 'capture') {
    capturePage();
  }
});

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', capturePage);
} else {
  capturePage();
}
