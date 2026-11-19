// Pure release selection for browser and Node regression tests.
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.BasketballRelease = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const pattern = /^[a-f0-9]{16}-[a-f0-9]{16}$/;
  function select(refresh) {
    if (!refresh || refresh.release == null) return null;
    if (typeof refresh.release !== 'string' || !pattern.test(refresh.release))
      throw new Error('Invalid private release identifier');
    return refresh.release;
  }
  function url(mode, release) {
    const file = mode === 'players' ? 'players' : 'teams';
    return 'data/' + file + '.json' + (release ? '?release=' + encodeURIComponent(release) : '');
  }
  function verify(data, release) {
    if (release && data?.release !== release)
      throw new Error('Dataset release does not match pinned refresh status');
  }
  return { select, url, verify };
});
