/**
 * Transform to fix template variable interpolation in Svelte components
 */
module.exports = function(fileInfo, api) {
  const j = api.jscodeshift;
  const src = fileInfo.source;
  
  // We need to handle the file content as text since jscodeshift doesn't parse Svelte files natively
  let result = src;
  
  // Fix template variable interpolation with ${} -> {}
  result = result.replace(/style="filter: \${([^}]+)}/g, 'style="filter: {$1}');
  
  // Fix other template literals in style attributes
  result = result.replace(/style="([^"]*)\${([^}]+)}([^"]*)"/g, 'style="$1{$2}$3"');
  
  // Fix SVG attribute template issues like {20 -> {20}
  result = result.replace(/{(\d+)([,\s])/g, '{$1}$2');
  
  // Fix SVG math expressions like {Math.max(3, -> {Math.max(3, ...)}
  result = result.replace(/{(Math\.[a-zA-Z]+\([^{}]+)(?!\})([,\s])/g, '{$1}$2');
  
  // Handle {processedThumbnailUrl} and other variable interpolations
  result = result.replace(/(\w+)="{(\w+)}"/g, '$1={$2}');

  return result;
};
