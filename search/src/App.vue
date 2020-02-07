<template>
  <div id="app">
    <div class="container">
      <div class="row">
        <form class="w-100" onsubmit="return false;">
          <div class="form-group">
            <label class="font-weight-bold" for="search">Search documents</label>
            <input class="form-control" id="search" v-model="query" placeholder="Type anything in here..." style="height: 50px" autofocus>
          </div>
        </form>
      </div>
      <div class="row mt-3 mb-2">
        <div class="col-2 card pb-4 h-100">
          <h5 class="font-weight-bold mt-4">Facets</h5>
          <div class="container mt-1" v-for="(facetsForGroup, facetGroupName) in facets">
            <hr class="mt-2 mb-2">
            <input class="form-check-input" type="checkbox" :id="facetGroupName" @change="toggleFacetGroup(facetGroupName)" v-model="selectedFacetGroups.includes(facetGroupName)">
            <label class="col-12 form-check-label ml-1 font-weight-bold" :for="facetGroupName">{{ facetGroupName }}</label>
            <div class="col-12 pr-0 mt-1 form-check form-check-inline" v-for="facet in facetsForGroup">
              <input class="form-check-input" type="checkbox" :id="facet" @change="toggleFacet(facet)" v-model="facetArray.includes(facet)">
              <label class="form-check-label ml-1" :for="facet">{{ facet }}</label>
            </div>
          </div>
        </div>
        <div class="col-10">
          <div class="mt-1 mb-2" v-if="query">Displaying <strong>{{ groupResults.length }}</strong> results found</div>

          <div class="card mt-3 w-100" v-for="r in groupResults">
            <a :href="r._source.link" target="_blank" class="result-link">
              <div class="card-body p-2 pl-3 pr-3">

                <!-- Title -->
                <h4 class="card-title mb-0">
                  <strong class="result-title mb-0" v-html="highlight(r._source.title, r.highlight.title)"></strong>
                  <h6 class="float-right mt-0 mb-0 result-subtitle">{{ r._source.facet_name }}</h6>
                </h4>

                <!-- h1, h2 and h3 -->
                <h4 class="mt-0 mb-1" v-if="displayBreadcrumb(r._source, r.highlight)">
                  <span class="m-0 result-subtitle hash"># </span>
                  <span class="m-0 result-subtitle" v-html="displayBreadcrumb(r._source, r.highlight)"></span>
                </h4>

                <!-- Paragraph -->
                <div class="p-2 pl-3 pr-3 markdown-body" v-if="r._source.type !== 'header' && r._source.type !== 'title'"
                     v-html="highlight(r._source.rendered_content, r.highlight.content, paragraph=true)"></div>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import _ from 'lodash'

  export default {
    name: 'app',
    computed: {
      groupResults() {
        const goupByTitle = (r) => {
          // We only go down up to h3
          let key = r._source.facet_name + ' / ' + r._source.title;
          key += r._source.h1 ? '/' + r._source.h1 : '';
          key += r._source.h2 ? '/' + r._source.h2 : '';
          key += r._source.h3 ? '/' + r._source.h3 : '';
          return key;
        };

        // We group all the results together based on the h3 heading path
        let groupedResults = this.$_.groupBy(this.results, goupByTitle);

        // We only show the most relevant of this heading and don't go further
        // This prevent from showing multiple part of the document for the same h3 (only show the most relevant)
        let results = Object.values(groupedResults).map(results => results[0]);

        // We regroup all the documents that have the same score then
        results = this.$_.groupBy(results, r => [r._source.title, r._score]);

        // We take the document that is a title or the first one
        results = Object.values(results).map(results => {
          const title = results.filter(r => r._source.type === 'title');
          const best_result = title.length !== 0 ? title[0] : results[0];
          return best_result;
        });

        return results
      },

      facetArray () {
        return this.getFacetArray();
      }
    },
    data() {
      return {
        query: this.$route.query.q || '',
        results: [],
        facets: {},
        selectedFacets: this.$route.query.facets || '',
        selectedFacetGroups: [],
        hitCount: null
      }
    },
    created() {
      this.getFacets();
      this.refresh();
    },
    watch: {
      query: 'refresh',
      selectedFacets: 'refresh'
    },
    methods: {
      refresh () {
        this.makeQuery();
      },
      makeQuery: _.debounce(function query() {
          const query = this.query;
          const facets = this.getFacetArray();
          const facetQueryString = this.selectedFacets;

          // Update the query path
          this.$router.push({query: {facets: facetQueryString, q: query}});

          // Make a search call
          this.$http.post('/api/search', {
            query: query,
            facets: facets

          }).then(response => {
            const data = response.data;
            this.results = data.hits.hits;
            this.hitCount = data.hits.total.value;

          }, error => {
            this.$bvToast.toast(`An error occured while searching for ${this.query}`, {
              title: 'Error',
              variant: 'danger'
            })
          });
        }, 300)
      ,
      getFacets () {
        this.$http.get('/api/facets').then(response => {
          this.facets = response.data;
        }, error => {
          this.$bvToast.toast(`An error occured while getting facets`, {
            title: 'Warning',
            variant: 'warning'
          })
        });
      },
      displayBreadcrumb(source, highlight) {
        // We only go down up to h3
        let titles = [
          highlight ? this.highlight(source.h1, highlight.h1) : source.h1,
          highlight ? this.highlight(source.h2, highlight.h2) : source.h2,
          highlight ? this.highlight(source.h3, highlight.h3) : source.h3,
        ];

        return titles.filter(Boolean).join(' > ')
      },
      highlight(renderedContent, highlightWords, paragraph=false) {
        if (!highlightWords) {
          return renderedContent;
        }

        // We join like this we get all the highlighted words together in a string to extract them
        highlightWords = highlightWords.join(' ');

        const wordMatched = [...new Set([...highlightWords.matchAll('<em>(.*?)<\/em>')].map(m => m[1]))];
        let highlightedRenderedContent = renderedContent;

        wordMatched.map(word => {
          const cssClass = paragraph ? 'hglt-txt' : 'hglt';

          try {
            highlightedRenderedContent = highlightedRenderedContent.replace(
              new RegExp(word + '(?![^<]\\*?>)', "g"), // do not replace in url within link tags i.e. <a href="url"></a>
              `<em class="${cssClass}">${word}</em>`
            );
          } catch(err) {
            console.log(err) // FIXME: regex does not work sometimes when special characters are used
          }
        });

        return highlightedRenderedContent;
      },
      toggleFacetGroup(facetGroup) {
        let facetsForGroup = this.facets[facetGroup];

        if (this.selectedFacetGroups.includes(facetGroup)) {
          this.selectedFacetGroups = this.selectedFacetGroups.filter(j => j !== facetGroup);
          facetsForGroup.forEach(f => this.removeFacet(f))
        } else {
          this.selectedFacetGroups.push(facetGroup);
          facetsForGroup.forEach(f => this.addFacet(f));
        }
      },
      toggleFacet(facet) {
        if (this.getFacetArray().includes(facet)) {
          this.removeFacet(facet)
        } else {
          this.addFacet(facet)
        }
      },
      addFacet(facet) {
        let newFacets = this.getFacetArray();
        newFacets.push(facet);
        this.selectedFacets = newFacets.join(',');
      },
      removeFacet(facet) {
        this.selectedFacets = this.getFacetArray().filter(f => f !== facet).join(',');
      },
      getFacetArray() {
        return this.selectedFacets === "" ? [] : this.selectedFacets.split(',');
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
    margin-top: 30px;
  }

  .hglt {
    font-style: normal;
    font-weight: bold;
    color: #de422f;
    background-color: #ffbcbca3;
    padding: 3px;
  }

  .hglt-txt {
    font-style: normal;
    font-weight: 900;
    color: rgb(36, 41, 46);;
  }

  .hash {
    color: #de422f !important;
  }

  p {
    margin: 0 !important;
  }

  .result-link {
    text-decoration: none !important;
  }

  .result-title {
    color: #24292e;;
    font-weight: 900 !important;
    font-size: 1rem;
  }

  .result-subtitle {
    color: #24292e;;
    /*font-weight: 900 !important;*/
    font-size: 1rem;
  }

</style>
