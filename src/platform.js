// global references to browser objects
let wakeLockObj;
let wakeLockRequest;


// how does JS not have this
function map (obj, f) {
  return Object.keys(obj).map((key) => f(key, obj[key]))
}

// oh the humanity
function copy (obj) {
  return JSON.parse(JSON.stringify(obj))
}

// toggle fullscreen, with x-browser support
function toggleFullScreen() {
  var doc = window.document;
  var docEl = doc.documentElement;

  var requestFullScreen = docEl.requestFullscreen || docEl.mozRequestFullScreen || docEl.webkitRequestFullScreen || docEl.msRequestFullscreen;
  var cancelFullScreen = doc.exitFullscreen || doc.mozCancelFullScreen || doc.webkitExitFullscreen || doc.msExitFullscreen;

  if(!doc.fullscreenElement && !doc.mozFullScreenElement && !doc.webkitFullscreenElement && !doc.msFullscreenElement) {
    requestFullScreen.call(docEl);
  }
  else {
    cancelFullScreen.call(doc);
  }
}

// ensure exiting full screen mode kills the wakelock
function onFullScreenChange(ev) {
  console.log('fullscreen:', Boolean(document.fullscreenElement))
  if (wakeLockRequest && !document.fullscreenElement) {
    wakeLockRequest.cancel();
    wakeLockRequest = null;
    console.log('cancelled wakelock as exiting fullscreen')
  }
}
document.addEventListener('fullscreenchange', onFullScreenChange)
document.addEventListener('fullscreenerror', (err) => { console.error(err) })

// setup the wakelock once we have it
function initialiseWakeLock(lock) {
    wakeLockObj = lock;
    wakeLockObj.addEventListener('activechange', () => {
        console.log('⏰', 'wakeLock active:', wakeLockObj.active,);
    })
    console.log('👍', 'getWakeLock', wakeLockObj);
}

function toggleWakeLock() {
  if (wakeLockObj) {
    if (wakeLockRequest) {
      wakeLockRequest.cancel();
      wakeLockRequest = null;
      return;
    }
    wakeLockRequest = wakeLockObj.createRequest();
  }
}


// getting a wakelock involves a promise, because $REASONS
if ('getWakeLock' in navigator) {
  navigator.getWakeLock('screen')
    .then(initialiseWakeLock)
    .catch(err => console.error('👎', 'getWakeLock', err))
} else {
  console.log('getWakeLock not supported')
  // TODO: if chrome, link user to chrome://flags/#enable-experimental-web-platform-features
  // otherwise, try https://github.com/richtr/NoSleep.js
}

export {
  map,
  copy,
  toggleFullScreen,
  toggleWakeLock,
}
