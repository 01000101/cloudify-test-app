var gulp = require('gulp');
var connect = require('gulp-connect');
var minifyCss = require('gulp-minify-css');
var concat = require('gulp-concat');
var minifyJs = require('gulp-uglify');
var rename = require('gulp-rename');
var convertYaml = require('gulp-yaml');

var css = {
	dest: './assets/css/dist',
	base: './',
	files: [
		'./assets/css/*.css'
	]
};

var js = {
	dest: './assets/js/dist',
	base: './',
	files: [
		'./app/app.js',
		'./app/services/*.js',
		'./app/shared/*/*.js',
		'./app/components/*/*.js'
	]
};

var yaml = {
	dest: './assets/yaml/dist',
	base: './',
	files: [
		'./assets/yaml/*.yaml'
	]
};

gulp.task('serve', function() {
    connect.server({
        root: './',
        host: 'localhost',
        port: 6969,
        fallback: 'index.html',
        livereload: true
    });
});

gulp.task('minify-css', function() {
	return gulp.src(css.files, {base: css.base})
		.pipe(minifyCss())
		.pipe(rename({
			suffix: '.min'
		}))
		.pipe(concat('bundle.min.css'))
		.pipe(gulp.dest(css.dest));
});

gulp.task('minify-js', function() {
	return gulp.src(js.files, {base: js.base})
		.pipe(minifyJs())
		.pipe(rename({
			suffix: '.min'
		}))
		.pipe(concat('bundle.min.js'))
		.pipe(gulp.dest(js.dest));
});

gulp.task('convert-yaml', function() {
	return gulp.src(yaml.files)
		.pipe(convertYaml({space: 2}))
		.pipe(gulp.dest(yaml.dest));
});

gulp.task('watch', function() {
	gulp.watch(css.files, ['minify-css']);
	gulp.watch(js.files, ['minify-js']);
});

gulp.task('default',
	[
		'minify-css', 'minify-js',
		'convert-yaml',
		'watch', 'serve'
	], function() {
	
});