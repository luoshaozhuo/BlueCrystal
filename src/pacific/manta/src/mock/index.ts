import Mock from 'mockjs';

import './user';
import './message';
import './windfarm';
import './user-center';
import './data-acquisition';
import './lidar';
import './load-mitigation';
import './power-analysis';

function patchMockJsPassthroughResponseType() {
  const mockXhr = (
    Mock as typeof Mock & {
      XHR?: {
        prototype?: {
          send?: (data?: Document | XMLHttpRequestBodyInit | null) => void;
          __showtimePatchedResponseTypePassthrough__?: boolean;
          match?: boolean;
          responseType?: XMLHttpRequestResponseType;
          custom?: {
            xhr?: XMLHttpRequest;
          };
        };
      };
    }
  ).XHR;

  const prototype = mockXhr?.prototype;
  if (
    !prototype ||
    prototype.__showtimePatchedResponseTypePassthrough__ ||
    typeof prototype.send !== 'function'
  ) {
    return;
  }

  const originalSend = prototype.send;
  prototype.send = function patchedSend(
    this: {
      match?: boolean;
      responseType?: XMLHttpRequestResponseType;
      custom?: {
        xhr?: XMLHttpRequest;
      };
    },
    data?: Document | XMLHttpRequestBodyInit | null,
  ) {
    if (!this.match && this.custom?.xhr && this.responseType) {
      try {
        this.custom.xhr.responseType = this.responseType;
      } catch (error) {
        console.warn(
          'Failed to preserve native XHR responseType for mock passthrough.',
          error,
        );
      }
    }

    return originalSend.call(this, data);
  };
  prototype.__showtimePatchedResponseTypePassthrough__ = true;
}

patchMockJsPassthroughResponseType();

Mock.setup({
  timeout: '600-1000',
});
