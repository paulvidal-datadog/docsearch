const webpack = require('webpack');

module.exports = {
  runtimeCompiler: true,
  configureWebpack: {
    plugins: [
      new webpack.ProvidePlugin({
        $: 'jquery',
        jquery: 'jquery',
        jQuery: 'jquery',
        'window.jQuery': 'jquery'
      })
    ]
  },
  outputDir: '../static',
  assetsDir: 'assets',

  // Only used for the dev server
  devServer: {
    disableHostCheck: true,
    // This proxies all the calls to flask that start with a /api (makes it look like we only have 1 origin)
    proxy: {
      '^/api': {
        target: 'http://localhost:5000',
        ws: true,
        changeOrigin: true,
        followRedirects: true,
      }
    }
  }
};