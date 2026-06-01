function renderNativeSketch() {
  const container = document.getElementById('sketch-frame');
  if (!container) return;
  container.innerHTML = ''; // clear

  if (!sketchElements || sketchElements.length === 0) return;

  // Find bounding box to ensure container is large enough
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  sketchElements.forEach(el => {
    if (el.x < minX) minX = el.x;
    if (el.y < minY) minY = el.y;
    if (el.x + (el.width || 0) > maxX) maxX = el.x + (el.width || 0);
    if (el.y + (el.height || 0) > maxY) maxY = el.y + (el.height || 0);
  });

  // Add some padding
  const padding = 50;
  const contentWidth = Math.max(maxX + padding, container.clientWidth);
  const contentHeight = Math.max(maxY + padding, container.clientHeight);
  
  const canvas = document.createElement('div');
  canvas.style.position = 'relative';
  canvas.style.width = contentWidth + 'px';
  canvas.style.height = contentHeight + 'px';
  canvas.style.backgroundColor = '#1e1e1e'; // Dark theme background

  sketchElements.forEach(el => {
    const div = document.createElement('div');
    div.style.position = 'absolute';
    div.style.left = el.x + 'px';
    div.style.top = el.y + 'px';
    div.style.width = (el.width || 0) + 'px';
    div.style.height = (el.height || 0) + 'px';
    div.style.pointerEvents = 'none'; // pass through clicks

    if (el.type === 'rectangle') {
      div.style.backgroundColor = el.backgroundColor || 'transparent';
      div.style.border = `${el.strokeWidth || 1}px ${el.strokeStyle || 'solid'} ${el.strokeColor || '#000'}`;
      if (el.roundness) {
        div.style.borderRadius = '4px'; // simple approximation
      }
    } else if (el.type === 'text') {
      div.innerText = el.text || '';
      div.style.color = el.strokeColor || '#e8e8f0';
      div.style.fontSize = (el.fontSize || 12) + 'px';
      div.style.fontFamily = 'sans-serif';
      div.style.display = 'flex';
      
      // alignment
      if (el.textAlign === 'center') div.style.justifyContent = 'center';
      else if (el.textAlign === 'right') div.style.justifyContent = 'flex-end';
      else div.style.justifyContent = 'flex-start';
      
      if (el.verticalAlign === 'middle') div.style.alignItems = 'center';
      else if (el.verticalAlign === 'bottom') div.style.alignItems = 'flex-end';
      else div.style.alignItems = 'flex-start';
      
      div.style.whiteSpace = 'pre-wrap';
    }
    
    canvas.appendChild(div);
  });

  container.appendChild(canvas);
}
