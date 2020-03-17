function varargout = ismembc_octave(varargin)
  varargout = cell(nargout, 1);
  [varargout{:}] = ismember(varargin{:});
endfunction
