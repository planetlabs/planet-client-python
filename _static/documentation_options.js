var DOCUMENTATION_OPTIONS = {
    URL_ROOT: document.getElementById("documentation_options").getAttribute('data-url_root'),
    VERSION: '1.4.8',
    LANGUAGE: 'None',
    COLLAPSE_INDEX: false,
    BUILDER: 'html',
    FILE_SUFFIX: '.html',
    LINK_SUFFIX: '.html',
    HAS_SOURCE: true,
    SOURCELINK_SUFFIX: '.txt',
    NAVIGATION_WITH_KEYS: false
};

//Hack to redirect to v2 docs with as little changes as possible
window.onload = function() {
  r = document.getElementById('redirect')
  if (!r) {
    r = document.createElement('div')
    r.setAttribute('id', 'redirect')
    r.innerHTML = 'This is the documentation for version 1 of the Planet Python Client, which is deprecated. <br /> Please visit the <a href="https://planet-sdk-for-python-v2.readthedocs.io/en/stable/get-started/upgrading/">SDK v2 documentation</a> for instructions on how to upgrade.'
    document.body.prepend(r);
  }
}

