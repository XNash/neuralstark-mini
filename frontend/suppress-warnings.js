// Suppress specific deprecation warnings from webpack-dev-server
// These warnings come from react-scripts 5.0.1 using old webpack-dev-server API
const originalEmitWarning = process.emitWarning;
process.emitWarning = (warning, ...args) => {
  // Suppress webpack-dev-server middleware deprecation warnings
  if (
    warning && 
    typeof warning === 'string' && 
    (warning.includes('onAfterSetupMiddleware') || 
     warning.includes('onBeforeSetupMiddleware'))
  ) {
    return;
  }
  return originalEmitWarning.call(process, warning, ...args);
};
