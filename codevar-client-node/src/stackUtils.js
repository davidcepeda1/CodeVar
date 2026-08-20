const FRAME_PATTERN = /at (?:.*\()?([^()]+):(\d+):(\d+)\)?$/;

function extractExceptionInfo(err) {
  const stackTrace = err.stack || `${err.name}: ${err.message}`;
  const frameLine = stackTrace.split("\n").find((line) => FRAME_PATTERN.test(line));
  const match = frameLine ? frameLine.match(FRAME_PATTERN) : null;

  return {
    exceptionType: err.name || "Error",
    filePath: match ? match[1] : "unknown",
    lineNumber: match ? parseInt(match[2], 10) : 0,
    stackTrace,
  };
}

module.exports = { extractExceptionInfo };
