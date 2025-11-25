export class PolygonModel {
  points: [number, number][];

  constructor(points: [number, number][]) {
    this.points = points;
  }

  static distance(pointA: [number, number], pointB: [number, number]): number {
    return Math.sqrt(Math.pow(pointA[0] - pointB[0], 2) + Math.pow(pointA[1] - pointB[1], 2))
  }

  /**
   * Check if a given point is within the polygon. The polygon consists of an ordered list of interconnected points.
   * The algorithm used is the ray-casting algorithm (https://rosettacode.org/wiki/Ray-casting_algorithm).
   * It follows the coordinate conventions used by the HTML canvas component (https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API).
   *
   * @param x The x-coordinate of the point.
   * @param y The x-coordinate of the point.
   */
  pointIsInArea(x: number, y: number): boolean {
    let count = 0;
    for (let i = 0; i < this.points.length; i++) {
      if (this.rayIntersectsSegment([x, y], {start: this.points[i], end: this.points[(i + 1) % this.points.length]})) {
        count++;
      }
    }
    return (count % 2) !== 0;
  }

  rayIntersectsSegment(point: [number, number], segment: { start: [number, number]; end: [number, number] }): boolean {
    /*
    Point A below B (in case of canvas, this means that A.y > B.y)
    Function return true if:
    1. to the left of segment
    2. between startY and endY
     */
    if (segment.start[1] >= segment.end[1]) {
      if (point[1] > segment.start[1] || point[1] <= segment.end[1]
        || (point[0] >= segment.start[0] && point[0] >= segment.end[0])) {
        return false;
      } else if (point[0] < segment.start[0] && point[0] < segment.end[0]) {
        return true;
      } else {
        return (segment.start[1] - point[1]) / (point[0] - segment.start[0]) > (segment.end[1] - point[1]) / (point[0] - segment.end[0])
      }
    } else {
      return this.rayIntersectsSegment(point, {start: segment.end, end: segment.start});
    }
  }

  calcLines(): [number, number][] {
    let length = this.points.length;
    let lineList: [number, number][] = [];
    for (let i = 0; i < length; i++) {
      const point2 = this.points[(i + 1) % length];
      lineList.push([point2[0] - this.points[i][0], point2[1] - this.points[i][1]]);
    }
    return lineList;
  }


  centroid(): [number, number] {
    const lines = this.calcLines();
    const x = lines[0][0] * Math.cos(90) - lines[0][1] * Math.sin(90);
    const y = lines[0][0] * Math.sin(90) + lines[0][1] * Math.cos(90);
    return [this.first()[0] + lines[0][0], this.first()[1] + lines[1][0]];
    /*const firstPoint = this.first();
    let lastPoint = this.last();
    if (this.isLastPointFirst(6) && this.points.length > 3) {
      lastPoint = this.points[this.points.length - 2];
    }
    const vector = [lastPoint[0] - firstPoint[0], lastPoint[1] - firstPoint[1]];
    return [firstPoint[0] + 1 / 2 * vector[0], firstPoint[1] + 1 / 2 * vector[1]]*/
  }

  isLastPointFirst(distanceThreshold: number = 2): boolean {
    const start = this.points[0];
    const end = this.points[this.points.length - 1];
    return PolygonModel.distance(start, end) < distanceThreshold;
  }

  first(): [number, number] {
    return this.points[0];
  }

  last(): [number, number] {
    return this.points[this.points.length - 1];
  }
}

class Line {
  private point: [number, number];
  private vector: [number, number];


  constructor(point: [number, number], vector: [number, number]) {
    this.point = point;
    this.vector = vector;
  }
}
