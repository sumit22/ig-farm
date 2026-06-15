// Check if current URL is a profile page
function isProfilePage(url) {
  const match = url.match(/instagram\.com\/([^/?]+)\/?$/);
  return match && !['reels', 'explore', 'stories', 'accounts', 'direct'].includes(match[1]);
}

// Capture and send page
async function capturePage() {
  const url = window.location.href;
  
  if (!isProfilePage(url)) {
    console.log('Not a profile page');
    return;
  }

  const html = document.documentElement.outerHTML;
  const title = document.title;
  const capturedAt = new Date().toISOString();

  try {
    const response = await fetch('http://localhost:8000/api/capture', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url,
        html,
        title,
        captured_at: capturedAt,
      }),
    });

    const data = await response.json();
    
    if (data.status === 'ok' && data.next_profile) {
      // Wait random delay
      const delay = 3000 + Math.random() * 5000;
      setTimeout(() => {
        window.location.href = data.next_profile;
      }, delay);
    }
  } catch (error) {
    console.error('Capture failed:', error);
  }
}

// Run on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', capturePage);
} else {
  capturePage();
}
