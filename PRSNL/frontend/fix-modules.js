/**
 * Module Import/Export Fix Script
 * 
 * This script fixes issues with ES6 modules being served without proper script type="module"
 * by detecting script tags in Svelte files and ensuring they have the correct type attribute.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Directory to scan for Svelte files
const basePath = path.join(__dirname, 'src');

// Function to recursively get all Svelte files
function getAllSvelteFiles(dir) {
  let files = [];
  const items = fs.readdirSync(dir);

  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory()) {
      files = files.concat(getAllSvelteFiles(fullPath));
    } else if (item.endsWith('.svelte')) {
      files.push(fullPath);
    }
  }
  
  return files;
}

// Get all Svelte files
const svelteFiles = getAllSvelteFiles(basePath);
console.log(`Found ${svelteFiles.length} Svelte files to process`);

// Process each Svelte file
let fixedFiles = 0;
let fixedIssues = {
  moduleDeclarations: 0,
  templateInterpolation: 0,
  svgAttributes: 0,
  mathExpressions: 0
};

for (const filePath of svelteFiles) {
  let fileContent = fs.readFileSync(filePath, 'utf8');
  let originalContent = fileContent;
  let fileChanged = false;
  
  // Check for script tags without type="module"
  if (/<script\s+lang=['"]ts['"]\s*>/g.test(fileContent)) {
    // Replace with proper script tag
    fileContent = fileContent.replace(
      /<script\s+lang=['"]ts['"]\s*>/g,
      '<script lang="ts" type="module">'
    );
    
    if (fileContent !== originalContent) {
      fixedIssues.moduleDeclarations++;
      fileChanged = true;
      console.log(`Fixed module declaration in ${path.basename(filePath)}`);
    }
  }
  
  // Check for template variables that aren't properly interpolated
  if (/style="[^"]*\${[^}]+}[^"]*"/g.test(fileContent)) {
    // Replace with proper Svelte interpolation
    fileContent = fileContent.replace(
      /style="([^"]*)(\${([^}]+)})([^"]*)"/g,
      'style="$1{$3}$4"'
    );
    
    if (fileContent !== originalContent) {
      fixedIssues.templateInterpolation++;
      fileChanged = true;
      console.log(`Fixed template interpolation in ${path.basename(filePath)}`);
    }
  }
  
  // Fix SVG attribute issues with {...
  if (/{(\d+)([,\s])/g.test(fileContent)) {
    // Replace with proper curly braces
    fileContent = fileContent.replace(
      /{(\d+)([,\s])/g,
      '{$1}$2'
    );
    
    if (fileContent !== originalContent) {
      fixedIssues.svgAttributes++;
      fileChanged = true;
      console.log(`Fixed SVG attribute in ${path.basename(filePath)}`);
    }
  }
  
  // Fix Math expressions not being closed properly
  if (/{(Math\.[a-zA-Z]+\([^{}]+)(?!\})([,\s])/g.test(fileContent)) {
    // Replace with proper closing brace
    fileContent = fileContent.replace(
      /{(Math\.[a-zA-Z]+\([^{}]+)(?!\})([,\s])/g,
      '{$1}$2'
    );
    
    if (fileContent !== originalContent) {
      fixedIssues.mathExpressions++;
      fileChanged = true;
      console.log(`Fixed Math expression in ${path.basename(filePath)}`);
    }
  }
  
  if (fileChanged) {
    fs.writeFileSync(filePath, fileContent);
    fixedFiles++;
  }
}

console.log(`
Fix Summary:
- Module declarations fixed: ${fixedIssues.moduleDeclarations}
- Template interpolation issues fixed: ${fixedIssues.templateInterpolation}
- SVG attribute issues fixed: ${fixedIssues.svgAttributes}
- Math expression issues fixed: ${fixedIssues.mathExpressions}
- Total files modified: ${fixedFiles}
`);
