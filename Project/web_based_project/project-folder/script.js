const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const dropZone = document.getElementById('dropZone');
const previewPanel = document.getElementById('previewPanel');
const previewImage = document.getElementById('previewImage');
const opacitySlider = document.getElementById('opacity');
const statusElement = document.querySelector('.status');

// Paths for the detection results
const backgroundImagePath = "../detection_results/detected_hou3.jpg";
const coordinatesFilePath = "../detection_results/coordinates_hou3.txt";

let newImage = null;
let boxes = [];
let isDragging = false;
let isResizing = false;
let dragImage = null;
let dragStartX = 0;
let dragStartY = 0;
let currentBox = null;
let hoveredBox = null;
let currentOpacity = 1.0;
let placedImages = new Map(); // Store placed images with their box reference

// === Handle drag and drop file upload ===
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) {
    handleImageUpload(file);
  }
});

// === Handle file input ===
document.getElementById('newImageInput').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) {
    handleImageUpload(file);
  }
});

// === Handle image upload ===
function handleImageUpload(file) {
  const reader = new FileReader();
  reader.onload = function (event) {
    const img = new Image();
    img.onload = function () {
      newImage = img;
      statusElement.textContent = 'Image loaded - Click on a box to place';
    };
    img.src = event.target.result;
  };
  reader.readAsDataURL(file);
}

// === Load coordinates ===
async function loadCoordinates(path) {
  try {
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const text = await response.text();
    const boxes = [];

    const lines = text.trim().split('\n');
    for (const line of lines) {
      const match = line.match(/x1:(\d+)\s*y1:(\d+)\s*x2:(\d+)\s*y2:(\d+)\s*(\w+)?/);
      if (match) {
        const [x1, y1, x2, y2, type] = match.slice(1);
        boxes.push({ 
          x1: Number(x1), 
          y1: Number(y1), 
          x2: Number(x2), 
          y2: Number(y2),
          type: type || 'unknown',
          hasImage: false
        });
      }
    }
    console.log('Loaded boxes:', boxes);
    return boxes;
  } catch (error) {
    console.error('Error loading coordinates:', error);
    statusElement.textContent = 'Error loading coordinates file: ' + error.message;
    return [];
  }
}

// === Load image as HTMLImageElement ===
function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      console.log('Image loaded successfully:', src);
      resolve(img);
    };
    img.onerror = (error) => {
      console.error('Error loading image:', src, error);
      reject(new Error(`Failed to load image: ${src}`));
    };
    img.src = src;
  });
}

// === Draw functions ===
function drawBox(box, color = 'blue', lineWidth = 2) {
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.strokeRect(box.x1, box.y1, box.x2 - box.x1, box.y2 - box.y1);
  
  // Draw label
  ctx.fillStyle = color;
  ctx.font = '12px Arial';
  ctx.fillText(box.type, box.x1, box.y1 - 5);
}

function drawBoxes() {
  boxes.forEach(box => {
    const color = box.type === 'door' ? 'blue' : 'green';
    drawBox(box, color);
  });
}

// === Check if point is inside box ===
function isPointInBox(x, y, box) {
  return x >= box.x1 && x <= box.x2 && y >= box.y1 && y <= box.y2;
}

// === Get box at point ===
function getBoxAtPoint(x, y) {
  return boxes.find(box => isPointInBox(x, y, box));
}

// === Draw background and boxes ===
async function drawBackground() {
  try {
    console.log('Loading background image:', backgroundImagePath);
    const background = await loadImage(backgroundImagePath);
    canvas.width = background.width;
    canvas.height = background.height;
    ctx.drawImage(background, 0, 0);
    drawBoxes();
    console.log('Background drawn successfully');
  } catch (error) {
    console.error('Error drawing background:', error);
    statusElement.textContent = 'Error loading background image: ' + error.message;
  }
}

// === Handle opacity changes ===
opacitySlider.addEventListener('input', (e) => {
  currentOpacity = e.target.value / 100;
  redrawAll();
});

// === Draw placed images ===
function drawPlacedImages() {
  placedImages.forEach((imageData, boxId) => {
    const { image, box } = imageData;
    const boxWidth = box.x2 - box.x1;
    const boxHeight = box.y2 - box.y1;
    
    ctx.globalAlpha = currentOpacity;
    ctx.drawImage(
      image,
      box.x1,
      box.y1,
      boxWidth,
      boxHeight
    );
    ctx.globalAlpha = 1.0;
  });
}

// === Redraw all placed images ===
async function redrawAll() {
  await drawBackground();
  drawPlacedImages();
}

// === Handle mouse events ===
canvas.addEventListener('mousedown', (e) => {
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  if (!newImage) return;

  const box = getBoxAtPoint(x, y);
  if (box) {
    isDragging = true;
    currentBox = box;
    dragImage = newImage;
    previewImage.src = dragImage.src;
    previewPanel.style.display = 'block';
    
    // Immediately place the image in the box
    const boxWidth = box.x2 - box.x1;
    const boxHeight = box.y2 - box.y1;
    
    // Store the placed image
    placedImages.set(box.x1 + '_' + box.y1, {
      image: dragImage,
      box: box
    });
    
    box.hasImage = true;
    statusElement.textContent = `Image placed in ${box.type} box`;
    
    // Redraw everything
    redrawAll();
  }
});

canvas.addEventListener('mousemove', async (e) => {
  if (!isDragging || !dragImage || !currentBox) return;

  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  // Highlight the current box
  await drawBackground();
  drawBox(currentBox, 'yellow', 3);
  ctx.fillStyle = 'rgba(255, 255, 0, 0.1)';
  ctx.fillRect(currentBox.x1, currentBox.y1, currentBox.x2 - currentBox.x1, currentBox.y2 - currentBox.y1);
  
  // Draw the image
  const boxWidth = currentBox.x2 - currentBox.x1;
  const boxHeight = currentBox.y2 - currentBox.y1;
  
  ctx.globalAlpha = currentOpacity;
  ctx.drawImage(
    dragImage,
    currentBox.x1,
    currentBox.y1,
    boxWidth,
    boxHeight
  );
  ctx.globalAlpha = 1.0;
});

canvas.addEventListener('mouseup', async (e) => {
  if (!isDragging || !dragImage || !currentBox) return;

  // Reset drag state
  isDragging = false;
  dragImage = null;
  currentBox = null;
  previewPanel.style.display = 'none';

  // Redraw everything
  await redrawAll();
});

// Initialize
window.onload = async () => {
  try {
    console.log('Initializing application...');
    console.log('Loading coordinates from:', coordinatesFilePath);
    boxes = await loadCoordinates(coordinatesFilePath);
    console.log('Coordinates loaded, drawing background...');
    await drawBackground();
    statusElement.textContent = 'Ready to place images';
    console.log('Initialization complete');
  } catch (error) {
    console.error('Initialization error:', error);
    statusElement.textContent = 'Error initializing application: ' + error.message;
  }
};
