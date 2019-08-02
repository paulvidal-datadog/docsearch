import Vue from 'vue'
import App from './App.vue'
import router from './router'
import fontAwesome from './font-awesome'
import BootstrapVue from 'bootstrap-vue'
import _ from 'lodash';

import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import 'bootstrap/dist/js/bootstrap.js'

Vue.use(BootstrapVue);

// Import github css like stylesheet
import 'github-markdown-css/github-markdown.css'

// Add lodash
Object.defineProperty(Vue.prototype, '$_', { value: _ });

// Register font awesome component
Vue.component('font-awesome-icon', fontAwesome);

new Vue({
  render: h => h(App),
  router: router,
}).$mount('#app');
