<template>
  <div id="app">
    <div class="container">
      <div class="row">
        <form class="w-100" onsubmit="return false;">
          <div class="form-group">
            <label for="exampleInputEmail1">Search documents</label>
            <input class="form-control" id="exampleInputEmail1" v-model="query" placeholder="Search...">
          </div>
        </form>
      </div>

      <div class="row mt-2 mb-2">
        <div class="mt-1 mb-2">Displaying <strong>{{ groupResults.length }}</strong> file found</div>

        <div class="card mt-2 w-100" v-for="(r, i) in groupResults" @click="toggleVisibility(i)" style="cursor: pointer;">
          <div class="card-body markdown-body p-2 pl-3 pr-3">
            <h3 class="card-title">
              <font-awesome-icon :icon="reveal.includes(i) ? 'caret-down' : 'caret-right'" class="mr-1" />
              {{ r[0][0]._source.source + ' /'}}
              <a :href="r[0][0]._source.base_link" target="_blank" @click="toggleVisibility(i)" v-html="highlight(r[0][0]._source.title, r[0][0].highlight.title)"></a>
              <h6 class="float-right mt-0">{{ i + 1 }}</h6>
            </h3>
            <div v-for="(hit_r, j) in r" v-if="reveal.includes(i)">
              <a :href="hit_r[0]._source.link" target="_blank" @click="toggleVisibility(i)"><h4 class="card-subtitle" v-html="'# ' + displayBreadcrumb(hit_r[0]._source, hit_r[0].highlight)"></h4></a>
              <div v-for="o in hit_r">
                <div v-html="highlight(o._source.rendered_content, o.highlight.content)"></div>
              </div>
              <hr v-if="j !== r.length - 1"/>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import search from './query';

  export default {
    name: 'app',
    computed: {
      groupResults() {
        let groupedResults = this.$_.groupBy(this.results, r => r._source.source + ' / ' + r._source.title);
        // return groupedResults;
        groupedResults = this.$_.mapValues(groupedResults, groupResult => this.$_.groupBy(groupResult, hit => this.displayBreadcrumb(hit._source, hit.highlight)));
        return Object.values(groupedResults).map(h => Object.values(h))
      }
    },
    data() {
      return {
        query: '' || this.$route.query.q,
        results: [],
        reveal: [],
        hitCount: null
      }
    },
    created() {
      if (this.query) {
        this.makeQuery();
      }
    },
    watch: {
      query: 'makeQuery'
    },
    methods: {
      makeQuery () {
        // Update the query path
        this.$router.push({ query: { q: this.query } });

        // Make a search call
        search(this.query, (data) => {
          this.results = data.hits.hits;
          this.hitCount = data.hits.total.value;
        });
      },
      displayBreadcrumb(source, highlight) {
        let titles = [
          highlight ? this.highlight(source.h1, highlight.h1) : source.h1,
          highlight ? this.highlight(source.h2, highlight.h2) : source.h2,
          highlight ? this.highlight(source.h3, highlight.h3) : source.h3,
          highlight ? this.highlight(source.h4, highlight.h4) : source.h4,
          highlight ? this.highlight(source.h5, highlight.h5) : source.h5,
          highlight ? this.highlight(source.h6, highlight.h6) : source.h6
        ];

        return titles.filter(Boolean).join(' / ')
      },
      highlight(renderedContent, highlightWords) {
        if (!highlightWords) {
          return renderedContent;
        }

        // We join like this we get all the highlighted words together in a string to extract them
        highlightWords = highlightWords.join(' ');

        const wordMatched = [...new Set([...highlightWords.matchAll('<em>(.*?)<\/em>')].map(m => m[1]))];

        let highlightedRenderedContent = renderedContent;
        wordMatched.map(word => {
          try {
            highlightedRenderedContent = highlightedRenderedContent.replace(
              new RegExp(word + '(?![^<]\\*?>)', "g"), // do not replace in url within link tags i.e. <a href="url"></a>
              `<em class="hglt">${word}</em>`
            );
          } catch(err) {
            // TODO: fix this regex
            console.log(err)
          }
        });

        return highlightedRenderedContent;
      },
      toggleVisibility(i) {
        if (this.reveal.includes(i)) {
          this.reveal = this.reveal.filter(j => j !== i)
        } else {
          this.reveal.push(i)
        }
      }
    }
  }
</script>

<style lang="scss">
  #app {
    font-family: 'Avenir', Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-align: left;
    color: #2c3e50;
    margin-top: 60px;
  }

  .hglt {
    font-style: normal;
    font-weight: bold;
    color: #de422f;
    background-color: #ffbcbca3;
  }
</style>
