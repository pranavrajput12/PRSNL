/**
 * Module Import/Export Fix Script
 *
 * This script fixes issues with ES6 modules being served without proper script type="module"
 * by detecting script tags in Svelte files and ensuring they have the correct type attribute.
 */

import { Project } from 'ts-morph';
import fs from 'fs';
import path from 'path';

// Initialize a new TypeScript project
const project = new Project();

// Directory to scan for Svelte files
const basePath = path.join(__dirname, 'src');

// Function to recursively get all Svelte files
function getAllSvelteFiles(dir: string): string[] {
  let files: string[] = [];
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
for (const filePath of svelteFiles) {
  const fileContent = fs.readFileSync(filePath, 'utf8');

  // Check for script tags without type="module"
  const scriptRegex = /<script\s+lang=['"]ts['"]\s*>/g;
  if (scriptRegex.test(fileContent)) {
    // Replace with proper script tag
    const newContent = fileContent.replace(
      /<script\s+lang=['"]ts['"]\s*>/g,
      '<script lang="ts" type="module">'
    );

    if (newContent !== fileContent) {
      fs.writeFileSync(filePath, newContent);
      fixedFiles++;
      console.log(`Fixed module declaration in ${filePath}`);
    }
  }

  // Check for template variables that aren't properly interpolated
  const templateVarRegex = /style="[^"]*\${[^}]+}[^"]*"/g;
  if (templateVarRegex.test(fileContent)) {
    // Replace with proper Svelte interpolation
    const newContent = fileContent.replace(
      /style="([^"]*)(\${([^}]+)})([^"]*)"/g,
      'style="$1{$3}$4"'
    );

    if (newContent !== fileContent) {
      fs.writeFileSync(filePath, newContent);
      fixedFiles++;
      console.log(`Fixed template interpolation in ${filePath}`);
    }
  }

  // Fix SVG attribute issues with {...
  const svgRegex = /{(\d+)([,\s])/g;
  if (svgRegex.test(fileContent)) {
    // Replace with proper curly braces
    const newContent = fileContent.replace(/{(\d+)([,\s])/g, '{$1}$2');

    if (newContent !== fileContent) {
      fs.writeFileSync(filePath, newContent);
      fixedFiles++;
      console.log(`Fixed SVG attribute in ${filePath}`);
    }
  }

  // Fix Math expressions not being closed properly
  const mathRegex = /{(Math\.[a-zA-Z]+\([^{}]+)(?!\})([,\s])/g;
  if (mathRegex.test(fileContent)) {
    // Replace with proper closing brace
    const newContent = fileContent.replace(/{(Math\.[a-zA-Z]+\([^{}]+)(?!\})([,\s])/g, '{$1}$2');

    if (newContent !== fileContent) {
      fs.writeFileSync(filePath, newContent);
      fixedFiles++;
      console.log(`Fixed Math expression in ${filePath}`);
    }
  }
}

console.log(`Fixed module and template issues in ${fixedFiles} files`);
