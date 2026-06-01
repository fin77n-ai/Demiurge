function renderNativeSketch() {
  const container = document.getElementById('sketch-frame');
  if (!container) return;
  
  // Create or get canvas
  let canvas = document.getElementById('sketch-canvas');
  if (!canvas) {
    container.innerHTML = '';
    canvas = document.createElement('canvas');
    canvas.id = 'sketch-canvas';
    container.appendChild(canvas);
  }

  if (!sketchElements || sketchElements.length === 0) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    return;
  }

  // Calculate bounding box
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  sketchElements.forEach(el => {
    if (el.x < minX) minX = el.x;
    if (el.y < minY) minY = el.y;
    if (el.x + (el.width || 0) > maxX) maxX = el.x + (el.width || 0);
    if (el.y + (el.height || 0) > maxY) maxY = el.y + (el.height || 0);
  });

  const padding = 100;
  const contentWidth = Math.max(maxX + padding, container.clientWidth);
  const contentHeight = Math.max(maxY + padding, container.clientHeight);
  
  // Handle high DPI displays
  const dpr = window.devicePixelRatio || 1;
  canvas.style.width = contentWidth + 'px';
  canvas.style.height = contentHeight + 'px';
  canvas.width = contentWidth * dpr;
  canvas.height = contentHeight * dpr;

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  
  // Background
  ctx.fillStyle = '#1e1e1e';
  ctx.fillRect(0, 0, contentWidth, contentHeight);

  // Initialize RoughJS
  const rc = rough.canvas(canvas);

  sketchElements.forEach(el => {
    if (el.type === 'rectangle') {
      const options = {
        stroke: el.strokeColor || '#000',
        strokeWidth: el.strokeWidth || 1,
        fill: el.backgroundColor !== 'transparent' ? el.backgroundColor : null,
        fillStyle: el.fillStyle === 'solid' ? 'solid' : 'hachure',
        roughness: el.roughness !== undefined ? el.roughness : 1,
        bowing: 1,
        seed: el.seed || Math.floor(Math.random() * 100)
      };
      
      if (el.roundness) {
        // RoughJS doesn't natively support rounded rectangles easily, 
        // but we can draw a path or just use a standard rectangle for now
        rc.rectangle(el.x, el.y, el.width, el.height, options);
      } else {
        rc.rectangle(el.x, el.y, el.width, el.height, options);
      }
    } else if (el.type === 'text') {
      ctx.font = `${el.fontSize || 16}px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`;
      ctx.fillStyle = el.strokeColor || '#e8e8f0';
      ctx.textAlign = el.textAlign || 'left';
      ctx.textBaseline = el.verticalAlign === 'middle' ? 'middle' : 'top';
      
      let textX = el.x;
      let textY = el.y;

      if (el.textAlign === 'center') textX += el.width / 2;
      else if (el.textAlign === 'right') textX += el.width;

      if (el.verticalAlign === 'middle') textY += el.height / 2;

      ctx.fillText(el.text, textX, textY);
    }
  });
}
